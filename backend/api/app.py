"""FastAPI application factory.

- Ensures schema + default users on startup.
- Centralises JSON error responses (no tracebacks leak to clients).
- CORS restricted to configured dev origins.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router
from core.config import settings
from core.logging import configure_logging, get_logger
from model import registry

logger = get_logger()


def _model_ready_msg() -> str | None:
    reg = registry.load_registry(settings.MODEL_STORE_DIR)
    active = reg.get("active_model")
    if not active:
        return "No active model registered. Train one: python -m model.trainer"
    if not (settings.MODEL_STORE_DIR / active / "model.pkl").exists():
        return f"Active model {active} artifacts missing."
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    from db.migration import ensure_schema

    ensure_schema()
    msg = _model_ready_msg()
    if msg:
        logger.warning("MODEL NOT READY: %s", msg)
    else:
        logger.info("Model store ready, active model: %s", registry.load_registry(settings.MODEL_STORE_DIR)["active_model"])
    yield


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

# CORS: dev origins only. In production the React app is served behind the
# same Nginx, making these requests same-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs."},
    )