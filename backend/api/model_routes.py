"""Model lifecycle endpoints.

Read endpoints are available to any authenticated user; retrain and
activation require the admin role.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.security import admin_only, get_current_user
from core.config import settings
from core.logging import get_logger
from model import registry
from model.predictor import service as prediction_service

router = APIRouter(prefix="/model")
logger = get_logger()


@router.post("/retrain")
def retrain(user=Depends(admin_only)):
    logger.info("Retraining started by %s", user["sub"])
    from training.retrain import run_retrain

    result = run_retrain()
    prediction_service.flush()
    logger.info("Retraining finished by %s -> %s", user["sub"], result["version"])

    return {
        "version": result["version"],
        "promoted": result["promoted"],
        "reason": result["reason"],
        "active_model": result["active_model"],
        "metrics": result["metrics"],
    }


@router.post("/activate")
def activate(body: dict, user=Depends(admin_only)):
    version = body.get("version")
    if not version:
        raise HTTPException(status_code=422, detail="version is required")

    from training.retrain import activate as do_activate

    try:
        result = do_activate(version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    prediction_service.flush()
    return result


@router.get("/status")
def status(user=Depends(get_current_user)):
    reg = registry.load_registry(settings.MODEL_STORE_DIR)
    active = reg.get("active_model")
    if not active:
        return {"active_model": None, "history": [], "metrics": None}

    metadata = registry.read_version_json(settings.MODEL_STORE_DIR, active, "metadata.json") or {}
    metrics = registry.read_version_json(settings.MODEL_STORE_DIR, active, "metrics.json") or {}

    return {
        "active_model": active,
        "model_type": metadata.get("model_type"),
        "trained_at": metadata.get("trained_at"),
        "features": metadata.get("features"),
        "hyperparameters": metadata.get("hyperparameters"),
        "class_names": metadata.get("class_names"),
        "dataset": metadata.get("dataset"),
        "metrics": metrics,
        "history": reg.get("history", []),
    }


@router.get("/versions")
def versions(user=Depends(get_current_user)):
    reg = registry.load_registry(settings.MODEL_STORE_DIR)
    return {"active_model": reg.get("active_model"), "history": reg.get("history", [])}