from fastapi import APIRouter
from core.config import settings

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "alive", "environment": settings.ENV}

@router.get("/version")
def version():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION}