"""Single source of truth for model architecture.

Both the initial trainer and the retraining pipeline import from here so the
model configuration can never drift between them.
"""

# Order used for training, inference and storage. Never rely on accidental
# dictionary/array ordering; this list is authoritative.
FEATURE_ORDER = [
    "attendance",
    "internal_marks",
    "assignments",
    "study_hours",
    "backlog_count",
    "stress_level",
]

TARGET_COLUMN = "risk_level"

CLASS_NAMES = {0: "ADVANCE", 1: "HOLD", 2: "RETREAT"}
ACTIONS = ("ADVANCE", "HOLD", "RETREAT")

MODEL_CONFIG = {
    "model_type": "RandomForestClassifier",
    "n_estimators": 200,
    "max_depth": 8,
    "class_weight": {0: 2.5, 1: 1.0, 2: 1.2},
    "random_state": 42,
    "n_jobs": -1,
}

TRAIN_TEST_SPLIT = {"test_size": 0.2, "random_state": 42}

# Promotion policy: a candidate is auto-activated only when its macro F1 is
# >= the active model's macro F1 minus this tolerance. Otherwise it is
# registered but left inactive.
PROMOTION_TOLERANCE = 0.01

DATASET_DESCRIPTION = (
    "Synthetic student records generated for development/demo. "
    "Not real-world student data."
)