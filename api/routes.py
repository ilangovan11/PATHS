from fastapi import APIRouter
from api.health import router as health_router
from api.auth_routes import router as auth_router
from api.decision_routes import router as decision_router
from api.analytics_routes import router as analytics_router

router = APIRouter()

router.include_router(health_router)
router.include_router(auth_router)
router.include_router(decision_router)
router.include_router(analytics_router)