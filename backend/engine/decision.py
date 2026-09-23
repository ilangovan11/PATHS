"""Decision orchestration: preprocessing -> ML prediction -> safety rules.

Produces the final decision plus a truthful execution trace, the model
version used, class probabilities, and model-level feature importance.
"""

from engine.paths_logic import evaluate_rules
from model.config import CLASS_NAMES
from model.predictor import service as prediction_service


def coordinate(raw_input) -> dict:
    raw = [float(v) for v in raw_input]

    prediction = prediction_service.predict(raw)
    prediction_label = prediction["prediction_class"]
    confidence = prediction["confidence"]

    action, reason, rules_checked = evaluate_rules(prediction_label, confidence, raw)

    trace = [
        "Input validated against documented feature ranges.",
        f"Features scaled using the active model's StandardScaler "
        f"(model {prediction['model_version']}).",
        f"Model prediction: {prediction_label} "
        f"(confidence {round(confidence, 3)}).",
        "Safety rules evaluated.",
        f"Final action: {action}.",
    ]

    return {
        "prediction": prediction_label,
        "action": action,
        "confidence": round(confidence, 4),
        "reason": reason,
        "model_version": prediction["model_version"],
        "probabilities": prediction["probabilities"],
        "class_names": {str(k): v for k, v in CLASS_NAMES.items()},
        "rules_checked": rules_checked,
        "trace": trace,
        "feature_importances": prediction_service.feature_importances(),
    }