from fastapi import APIRouter, Depends
from auth.security import admin_only
import json
import subprocess

router = APIRouter(prefix="/model")

@router.post("/retrain")
def retrain(user=Depends(admin_only)):
    subprocess.run(["python", "training/retrain.py"])
    return {"status": "retrained"}

@router.get("/status")
def status(user=Depends(admin_only)):
    with open("model_store/registry.json") as f:
        return json.load(f)