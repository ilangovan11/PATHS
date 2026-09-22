"""Prediction service.

Thread-safe, cached model loading with automatic hot reload: the active
model's registry file is statted on each call; when its mtime or the active
version changes, the in-memory cache is rebuilt. This fixes the v1.0 defect
where retraining changed artifacts but the running process kept serving the
old model.
"""

import json
import os
import threading
from pathlib import Path

import joblib
import pandas as pd

from model.config import CLASS_NAMES, FEATURE_ORDER
from core.config import settings
from core.logging import get_logger
from utils.metrics import probs_per_class

logger = get_logger()


class PredictionService:
    def __init__(self, store_dir):
        self.store_dir = Path(store_dir)
        self._lock = threading.Lock()
        self._cache = {
            "registry_mtime": None,
            "version": None,
            "model": None,
            "scaler": None,
        }

    # --- internal loading -------------------------------------------------

    def _registry_path(self) -> Path:
        return self.store_dir / "registry.json"

    def _load(self):
        registry_path = self._registry_path()
        if not registry_path.exists():
            raise FileNotFoundError(
                "No model registry found. Train a model first "
                f"(expected {registry_path})."
            )

        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
        version = registry.get("active_model")
        if not version:
            raise RuntimeError("Registry has no active model.")

        version_dir = self.store_dir / version
        model = joblib.load(version_dir / "model.pkl")
        scaler = joblib.load(version_dir / "scaler.pkl")
        logger.info("Loaded serving model %s from %s", version, version_dir)
        return version, model, scaler

    def _ensure_fresh(self):
        registry_path = self._registry_path()
        try:
            mtime = os.stat(registry_path).st_mtime
        except FileNotFoundError:
            self._cache = {"registry_mtime": None, "version": None, "model": None, "scaler": None}
            return
        if self._cache["registry_mtime"] == mtime and self._cache["model"] is not None:
            return
        with self._lock:
            # re-check inside lock to avoid double load by racing callers
            try:
                current_mtime = os.stat(registry_path).st_mtime
            except FileNotFoundError:
                return
            if self._cache["registry_mtime"] == current_mtime and self._cache["model"] is not None:
                return
            version, model, scaler = self._load()
            self._cache = {"registry_mtime": current_mtime, "version": version, "model": model, "scaler": scaler}

    # --- public API -------------------------------------------------------

    def get(self):
        self._ensure_fresh()
        return self._cache

    def predict(self, raw_input):
        """Return prediction info for a validated 6-feature input."""
        cache = self.get()
        model, scaler, version = cache["model"], cache["scaler"], cache["version"]

        # Build a labelled frame using the authoritative feature order so
        # scaling is identical to training (fixes the v1.0 feature-name
        # warning and ordering drift).
        frame = pd.DataFrame([list(raw_input)], columns=FEATURE_ORDER)
        scaled = scaler.transform(frame)

        probs = model.predict_proba(scaled)[0]
        cls_index = int(probs.argmax())
        label = CLASS_NAMES[int(model.classes_[cls_index])]

        return {
            "prediction_class": label,
            "confidence": float(probs[cls_index]),
            "probabilities": probs_per_class(model, probs),
            "model_version": version,
        }

    def feature_importances(self):
        model = self.get()["model"]
        return [
            {"feature": name, "importance": round(float(imp), 4)}
            for name, imp in zip(FEATURE_ORDER, model.feature_importances_)
        ]

    def flush(self):
        """Clear the cache (used by tests and retraining flows)."""
        with self._lock:
            self._cache = {"registry_mtime": None, "version": None, "model": None, "scaler": None}


service = PredictionService(settings.MODEL_STORE_DIR)