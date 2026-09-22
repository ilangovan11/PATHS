"""Model evaluation helpers.

Produces a comprehensive metric set (not just accuracy) from an actual
executed evaluation.
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def evaluate_model(model, X_test, y_test, feature_names, class_names) -> dict:
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)

    report = classification_report(y_test, preds, output_dict=True, zero_division=0)
    confusion = confusion_matrix(y_test, preds).tolist()

    feature_importances = [
        {"feature": name, "importance": round(float(imp), 4)}
        for name, imp in zip(feature_names, model.feature_importances_)
    ]
    feature_importances.sort(key=lambda item: item["importance"], reverse=True)

    return {
        "accuracy": round(float(accuracy_score(y_test, preds)), 4),
        "precision_macro": round(float(precision_score(y_test, preds, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_test, preds, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_test, preds, average="macro", zero_division=0)), 4),
        "per_class": {
            class_names[int(k)]: {m: round(float(v[m]), 4) for m in ("precision", "recall", "f1-score", "support")}
            for k, v in report.items()
            if k in class_names
        },
        "confusion_matrix": confusion,
        "class_names": list(class_names.values()),
        "mean_confidence": round(float(probs.max(axis=1).mean()), 4),
        "feature_importances": feature_importances,
        "n_samples_eval": int(len(y_test)),
    }


def report_summary(metrics: dict) -> str:
    return (
        f"accuracy={metrics['accuracy']} "
        f"f1_macro={metrics['f1_macro']} "
        f"precision_macro={metrics['precision_macro']} "
        f"recall_macro={metrics['recall_macro']}"
    )


def probs_per_class(model, probs_row: np.ndarray) -> dict:
    """Map a probability row to {class_name: probability} in model order."""
    classes = model.classes_.tolist()
    return {str(int(c)): round(float(p), 4) for c, p in zip(classes, probs_row)}