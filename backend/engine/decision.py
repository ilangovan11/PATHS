from model.predictor import predict
from engine.paths_logic import resolve_action

LABEL_MAP = {
    0: "ADVANCE",
    1: "HOLD",
    2: "RETREAT"
}

def coordinate(raw_input):
    prediction, confidence = predict(raw_input)
    action, reason = resolve_action(prediction, confidence, raw_input)

    return {
        "prediction": LABEL_MAP[prediction],
        "action": action,
        "confidence": round(confidence, 2),
        "reason": reason
    }