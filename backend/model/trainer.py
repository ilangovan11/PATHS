"""Single training pipeline.

Used by both initial training (``python -m model.trainer``) and the
retraining flow (``training/retrain.py``) so the configuration can never
diverge (v1.0 defect: trainer and retrainer used different hyperparameters).
"""

import json
from datetime import datetime, timezone

from sklearn.ensemble import RandomForestClassifier

from model import registry
from model.config import (
    CLASS_NAMES,
    DATASET_DESCRIPTION,
    FEATURE_ORDER,
    MODEL_CONFIG,
    PROMOTION_TOLERANCE,
)
from core.config import settings
from core.logging import get_logger
from utils.metrics import evaluate_model, report_summary
from utils.preprocess import fit_scaler, load_and_split

logger = get_logger()


def train(data_path: str, store_dir=None):
    """Train, evaluate and register a model version.

    Promotion policy: the candidate is activated only when its macro F1 is
    within PROMOTION_TOLERANCE of the currently active model's macro F1.
    Otherwise it is stored and registered as inactive (explicit activation
    can still promote it).
    """
    store_dir = store_dir or settings.MODEL_STORE_DIR
    store_dir.mkdir(parents=True, exist_ok=True)

    X_train, X_test, y_train, y_test = load_and_split(data_path)

    scaler = fit_scaler(X_train)
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=MODEL_CONFIG["n_estimators"],
        max_depth=MODEL_CONFIG["max_depth"],
        class_weight=MODEL_CONFIG["class_weight"],
        random_state=MODEL_CONFIG["random_state"],
        n_jobs=MODEL_CONFIG["n_jobs"],
    )
    model.fit(X_train_scaled, y_train)

    metrics = evaluate_model(
        model,
        X_test_scaled,
        y_test,
        feature_names=list(X_train.columns),
        class_names=CLASS_NAMES,
    )
    logger.info("Evaluation: %s", report_summary(metrics))

    version = registry.next_version(store_dir)
    trained_at = datetime.now(timezone.utc).isoformat()
    registry.save_model(store_dir, version, model, scaler)

    registry.write_version_json(
        store_dir,
        version,
        "metrics.json",
        metrics,
    )
    registry.write_version_json(
        store_dir,
        version,
        "metadata.json",
        {
            "version": version,
            "model_type": MODEL_CONFIG["model_type"],
            "trained_at": trained_at,
            "features": FEATURE_ORDER,
            "random_state": MODEL_CONFIG["random_state"],
            "hyperparameters": {
                k: v for k, v in MODEL_CONFIG.items() if k not in ("model_type",)
            },
            "class_names": CLASS_NAMES,
            "dataset": {
                "source": str(data_path),
                "description": DATASET_DESCRIPTION,
                "train_samples": int(len(X_train_scaled)),
                "eval_samples": int(len(X_test_scaled)),
            },
            "confidence_note": (
                "Confidence is the maximum class probability returned by the "
                "model and is not calibrated."
            ),
        },
    )

    active = registry.get_active_metadata(store_dir)
    f1_candidate = metrics["f1_macro"]
    if active is None:
        promote = True
        reason = "first registered version"
    else:
        active_f1 = (active.get("metrics") or {}).get("f1_macro")
        active_f1 = active_f1 if active_f1 is not None else 0.0
        promote = f1_candidate >= active_f1 - PROMOTION_TOLERANCE
        reason = (
            f"f1_candidate={f1_candidate} >= active_f1={active_f1} - tol"
            if promote
            else f"f1_candidate={f1_candidate} < active_f1={active_f1} - tol"
        )

    registry.register_version(
        store_dir,
        version,
        trained_at,
        accuracy=metrics["accuracy"],
        f1_macro=f1_candidate,
        active=promote,
    )

    logger.info("Version %s registered (promote=%s, %s)", version, promote, reason)
    if promote:
        logger.info("Model activation: %s is now active", version)

    return {
        "version": version,
        "promoted": promote,
        "reason": reason,
        "metrics": metrics,
        "active_model": store_dir and registry.load_registry(store_dir).get("active_model"),
    }


if __name__ == "__main__":
    result = train(settings.BACKEND_DATA_PATH)
    print(json.dumps({"version": result["version"], "promoted": result["promoted"], "metrics": result["metrics"]}, indent=2))