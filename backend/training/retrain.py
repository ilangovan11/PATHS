import json
import joblib
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from utils.preprocess import load_and_prepare

X_train, X_test, y_train, y_test = load_and_prepare("data/raw/student_data.csv")

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    random_state=42
)

model.fit(X_train, y_train)
acc = accuracy_score(y_test, model.predict(X_test))

with open("model_store/registry.json", "r") as f:
    registry = json.load(f)

version = f"v{len(registry['history']) + 2}.pkl"
joblib.dump(model, f"model_store/{version}")

registry["history"].append({
    "version": version,
    "accuracy": round(acc, 3),
    "trained_at": datetime.utcnow().isoformat()
})

registry["active_model"] = version

with open("model_store/registry.json", "w") as f:
    json.dump(registry, f, indent=2)

print("New model trained:", version)