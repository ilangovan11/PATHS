import joblib
import numpy as np

MODEL_PATH = "model/paths_model.pkl"
SCALER_PATH = "model/scaler.pkl"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

_model = None

def get_model():
    global _model
    if _model is None:
        _model = joblib.load("model/paths_model.pkl")
    return _model

def predict(input_data):
    """
    input_data: list or array in the SAME order as training features:
        [
            attendance,
            internal_marks,
            assignments,
            study_hours,
            backlog_count,
            stress_level
        ]
    """
    data = np.array(input_data, dtype=float).reshape(1, -1)

    data_scaled = scaler.transform(data)

    probs = model.predict_proba(data_scaled)[0]
    prediction = int(probs.argmax())
    confidence = float(probs[prediction])

    return prediction, confidence


if __name__ == "__main__":
    sample = [85, 78, 80, 5.0, 0, 3]
    pred, conf = predict(sample)
    print(f"Predicted risk_level: {pred}, confidence: {conf:.3f}")