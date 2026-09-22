from fastapi import APIRouter

from core.config import settings
from db.database import engine
from model import registry

router = APIRouter()


@router.get("/health")
def health():
    from sqlalchemy import text

    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    active = registry.load_registry(settings.MODEL_STORE_DIR).get("active_model")

    return {
        "status": "alive",
        "environment": settings.ENV,
        "database": "ok" if db_ok else "unavailable",
        "active_model": active,
    }


@router.get("/version")
def version():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION}