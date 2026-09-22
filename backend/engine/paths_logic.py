"""Deterministic safety-rule layer on top of the ML prediction.

Priority (unchanged from v1.0):
1. Critical risk override -> RETREAT
2. Low model confidence   -> HOLD
3. Model prediction map   -> ADVANCE / HOLD / RETREAT

Each rule evaluation is recorded so the API can expose which rules fired.
"""

from model.config import CLASS_NAMES


def evaluate_rules(prediction_label: str, confidence: float, features) -> tuple:
    attendance, _marks, _assignments, _study_hours, backlogs, stress = features

    rules_checked = []

    critical = attendance < 50 or (backlogs >= 5 and stress >= 8)
    rules_checked.append(
        {
            "rule": "critical_risk_override",
            "condition": "attendance < 50 OR (backlogs >= 5 AND stress >= 8)",
            "triggered": bool(critical),
        }
    )
    if critical:
        return "RETREAT", "Critical risk detected by rule override", rules_checked

    low_confidence = confidence < 0.6
    rules_checked.append(
        {
            "rule": "low_confidence_gate",
            "condition": "confidence < 0.6",
            "triggered": bool(low_confidence),
        }
    )
    if low_confidence:
        return "HOLD", "Low confidence in prediction", rules_checked

    rules_checked.append(
        {
            "rule": "model_prediction_map",
            "condition": f"model prediction is {prediction_label}",
            "triggered": True,
        }
    )
    if prediction_label == CLASS_NAMES[0]:
        return "ADVANCE", "Performance indicators are stable", rules_checked
    if prediction_label == CLASS_NAMES[1]:
        return "HOLD", "Moderate risk requires monitoring", rules_checked
    return "RETREAT", "High risk predicted by model", rules_checked