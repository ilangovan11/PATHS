import json
import joblib
import numpy as np

REGISTRY_PATH = "model_store/registry.json"
SCALER_PATH = "model/scaler.pkl"

_model = None
_scaler = None

def load_active_model():
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)
    return joblib.load(f"model_store/{registry['active_model']}")

def get_model():
    global _model
    if _model is None:
        _model = load_active_model()
    return _model

def get_scaler():
    global _scaler
    if _scaler is None:
        _scaler = joblib.load(SCALER_PATH)
    return _scaler

def predict(input_data):
    data = np.array(input_data, dtype=float).reshape(1, -1)

    scaler = get_scaler()
    model = get_model()

    data_scaled = scaler.transform(data)

    probs = model.predict_proba(data_scaled)[0]
    prediction = int(probs.argmax())
    confidence = float(probs[prediction])

    return prediction, confidence


if __name__ == "__main__":
    sample = [85, 78, 80, 5.0, 0, 3]
    pred, conf = predict(sample)
    print(f"Predicted risk_level: {pred}, confidence: {conf:.3f}")