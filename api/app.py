from fastapi import FastAPI
from api.routes import router
from core.config import settings

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)
