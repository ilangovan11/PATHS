"""Dataset loading and preprocessing.

All stages keep pandas column labels so that the StandardScaler is fitted and
used consistently with explicit feature names (eliminating the v1.0 feature-
name warning and any train/inference ordering drift).
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from model.config import FEATURE_ORDER, TARGET_COLUMN, TRAIN_TEST_SPLIT


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in FEATURE_ORDER + [TARGET_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")
    return df[FEATURE_ORDER + [TARGET_COLUMN]].copy()


def load_and_split(path: str):
    """Return (X_train, X_test, y_train, y_test) with explicit feature order.

    X frames are DataFrames labelled by FEATURE_ORDER; y are Series labelled
    with TARGET_COLUMN. Stratified split keeps class balance.
    """
    df = load_dataset(path)
    X = df[FEATURE_ORDER]
    y = df[TARGET_COLUMN]
    return train_test_split(
        X,
        y,
        test_size=TRAIN_TEST_SPLIT["test_size"],
        random_state=TRAIN_TEST_SPLIT["random_state"],
        stratify=y,
    )


def fit_scaler(X_train: pd.DataFrame) -> StandardScaler:
    scaler = StandardScaler()
    scaler.fit(X_train)  # fitted once, on training data only
    return scaler