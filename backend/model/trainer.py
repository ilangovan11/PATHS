import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from utils.preprocess import load_and_prepare

DATA_PATH = "data/raw/student_data.csv"
MODEL_PATH = "model/paths_model.pkl"

def main():
    X_train, X_test, y_train, y_test = load_and_prepare(DATA_PATH)

    model = RandomForestClassifier(
        n_estimators=200,
        class_weight={0: 2.5, 1: 1.0, 2: 1.2},
        max_depth=8,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, preds))
    print("\nClassification report:\n")
    print(classification_report(y_test, preds))

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()