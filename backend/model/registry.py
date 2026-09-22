"""Versioned model registry.

Layout (per version):
    <MODEL_STORE_DIR>/registry.json      - active version + history
    <MODEL_STORE_DIR>/<version>/model.pkl
    <MODEL_STORE_DIR>/<version>/scaler.pkl
    <MODEL_STORE_DIR>/<version>/metrics.json
    <MODEL_STORE_DIR>/<version>/metadata.json

The registry is the source of truth for which version is active and which
versions exist. Every file write is atomic (write-temp-then-rename).
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from threading import Lock

import joblib

from core.logging import get_logger

logger = get_logger()

_FILE_LOCK = Lock()


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    shutil.move(tmp, path)


def load_registry(store_dir: Path) -> dict:
    registry_path = store_dir / "registry.json"
    if not registry_path.exists():
        return {"active_model": None, "history": []}
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)
    registry.setdefault("active_model", None)
    registry.setdefault("history", [])
    return registry


def save_registry(store_dir: Path, registry: dict) -> None:
    _atomic_write_json(store_dir / "registry.json", registry)


def next_version(store_dir: Path) -> str:
    count = len([p for p in store_dir.iterdir() if p.is_dir() if p.name.startswith("v")])
    return f"v{count + 1}"


def save_model(store_dir: Path, version: str, model, scaler) -> Path:
    version_dir = store_dir / version
    version_dir.mkdir(parents=True, exist_ok=True)
    model_path = version_dir / "model.pkl"
    scaler_path = version_dir / "scaler.pkl"
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    return version_dir


def read_version_json(store_dir: Path, version: str, filename: str) -> dict | None:
    path = store_dir / version / filename
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_version_json(store_dir: Path, version: str, filename: str, payload: dict) -> None:
    version_dir = store_dir / version
    version_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(version_dir / filename, payload)


def get_active_metadata(store_dir: Path) -> dict | None:
    registry = load_registry(store_dir)
    active = registry.get("active_model")
    if not active:
        return None
    return {
        "version": active,
        "metadata": read_version_json(store_dir, active, "metadata.json"),
        "metrics": read_version_json(store_dir, active, "metrics.json"),
    }


def register_version(
    store_dir: Path,
    version: str,
    trained_at: str,
    accuracy: float,
    f1_macro: float,
    active: bool,
) -> None:
    with _FILE_LOCK:
        registry = load_registry(store_dir)
        entry = {
            "version": version,
            "trained_at": trained_at,
            "accuracy": round(accuracy, 4),
            "f1_macro": round(f1_macro, 4),
            "active": active,
        }
        # avoid duplicate history entries on re-registration
        registry["history"] = [e for e in registry["history"] if e["version"] != version]
        registry["history"].append(entry)
        if active:
            registry["active_model"] = version
            for e in registry["history"]:
                e["active"] = e["version"] == version
        save_registry(store_dir, registry)
        logger.info("Registered model version %s (active=%s)", version, active)