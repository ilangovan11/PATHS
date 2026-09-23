"""PATHS synthetic dataset generator (v2).

WHY V2 (root cause of the v1 defect)
------------------------------------
The v1 generator sampled features per class band and then applied 5% fully
random label noise. Two consequences made the classifier behave badly on
obviously-good students (e.g. 100/100/100/high study/0 backlog/low stress):

1. The training ranges had a low ceiling (max attendance 94, max marks 89)
   so a "perfect" student's vector was *outside* every leaf the Random
   Forest had seen, and RandomForest cannot extrapolate outside its training
   range.
2. Random label noise produced gross contradictions (e.g. a row with
   attendance 92 / marks 89 / assignments 92 / backlog 0 / stress 1 labelled
   RETREAT), poisoning the exact leaves a perfect student falls into.

V2 design
---------
Labels are computed from an explicit, documented latent score instead of
being sampled per band:

    perf   = 0.30*attendance/100 + 0.25*marks/100 + 0.20*assignments/100
           + 0.10*study_hours/16            (higher is better, weights sum 0.85)
    burden = 0.12*backlog_count/20 + 0.13*stress_level/10   (higher is worse)
    score  = perf - burden

    label  = ADVANCE (0) if score >= 0.50
             RETREAT (2) if score <= 0.26
             HOLD    (1) otherwise

Because the label is a deterministic function of the features, no row can
ever contradict the intended semantics (perfect inputs are always ADVANCE,
terrible inputs always RETREAT). Realistic overlap is created two ways:

* the latent "quality" q is drawn from a Beta+Uniform mixture whose random
  feature noise pushes many rows across the score thresholds, and
* a controlled ambiguity stage flips a label to its *adjacent* class with
  probability 0.20, but only for rows whose score is within 0.045 of a
  threshold (i.e. genuinely borderline rows). Gross contradictions are
  impossible by construction.

The full documented input domain is covered (0-100 percentages, study hours
up to 15.5, backlogs up to 20, stress 1-10) so inference never has to
extrapolate. Generation is deterministic (seed 42).
"""

from pathlib import Path

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "attendance",
    "internal_marks",
    "assignments",
    "study_hours",
    "backlog_count",
    "stress_level",
]

# Latent-score definition. Sum of perf weights = 0.85; document this in any
# report that cites the score so the scale is understood.
PERF_WEIGHTS = {"attendance": 0.30, "internal_marks": 0.25, "assignments": 0.20, "study_hours": 0.10}
PERF_DENOMS = {"attendance": 100.0, "internal_marks": 100.0, "assignments": 100.0, "study_hours": 16.0}
BURDEN_WEIGHTS = {"backlog_count": 0.12, "stress_level": 0.13}
BURDEN_DENOMS = {"backlog_count": 20.0, "stress_level": 10.0}

SCORE_ADVANCE_THRESHOLD = 0.50  # score >= this -> ADVANCE
SCORE_RETREAT_THRESHOLD = 0.26  # score <= this -> RETREAT
AMBIGUITY_MARGIN = 0.045        # rows within this of a threshold may flip
AMBIGUITY_FLIP_PROB = 0.20      # probability of the adjacent-class flip

OUTPUT_PATH = Path("data/raw/student_data.csv")


def _latent_score(df: pd.DataFrame) -> np.ndarray:
    perf = sum(
        PERF_WEIGHTS[c] * (df[c].to_numpy() / PERF_DENOMS[c]) for c in PERF_WEIGHTS
    )
    burden = sum(
        BURDEN_WEIGHTS[c] * (df[c].to_numpy() / BURDEN_DENOMS[c]) for c in BURDEN_WEIGHTS
    )
    return perf - burden


def generate(n: int = 700, seed: int = 42) -> pd.DataFrame:
    """Generate the synthetic student dataset (features + risk_level labels).

    Deterministic for a given (n, seed): all randomness is drawn from one
    ``default_rng(seed)`` local to this call.
    """
    r = np.random.default_rng(seed)

    # Draw a latent quality q in [0,1] with mass toward the middle/upper end.
    # 25% of rows are uniform so the extreme regions of the input domain are
    # covered densely enough for the model to learn them (this is what fixes
    # the v1 out-of-range/extrapolation problem for "perfect" students).
    draw = r.random(n)
    is_tail = draw < 0.25
    q = np.empty(n)
    q[is_tail] = r.uniform(0.0, 1.0, int(is_tail.sum()))
    q[~is_tail] = r.beta(2.2, 1.9, int((~is_tail).sum()))

    df = pd.DataFrame(
        {
            "attendance": np.clip(np.round(15 + 85 * q + r.normal(0, 8, n)), 0, 100).astype(int),
            "internal_marks": np.clip(np.round(13 + 87 * q + r.normal(0, 9, n)), 0, 100).astype(int),
            "assignments": np.clip(np.round(13 + 87 * q + r.normal(0, 10, n)), 0, 100).astype(int),
            "study_hours": np.clip(np.round((0.5 + 11 * q + r.normal(0, 1.2, n)) * 10) / 10, 0.5, 15.5),
            "backlog_count": np.clip(np.round(12 * (1 - q) + r.normal(0, 1.3, n)), 0, 20).astype(int),
            "stress_level": np.clip(np.round(2 + 8 * (1 - q) + r.normal(0, 1.3, n)), 1, 10).astype(int),
        }
    )
    score = _latent_score(df)
    labels = np.where(score >= SCORE_ADVANCE_THRESHOLD, 0, np.where(score <= SCORE_RETREAT_THRESHOLD, 2, 1)).astype(int)

    # Controlled ambiguity: only rows near a decision boundary may be flipped,
    # and only to the adjacent class (0<->1 or 1<->2).
    flip = r.random(n) < AMBIGUITY_FLIP_PROB
    near_advance = (score >= SCORE_ADVANCE_THRESHOLD - AMBIGUITY_MARGIN) & (
        score <= SCORE_ADVANCE_THRESHOLD + AMBIGUITY_MARGIN
    )
    near_retreat = (score >= SCORE_RETREAT_THRESHOLD - AMBIGUITY_MARGIN) & (
        score <= SCORE_RETREAT_THRESHOLD + AMBIGUITY_MARGIN
    )
    labels[near_advance & flip] = 1 - labels[near_advance & flip]
    retreat_zone = near_retreat & flip
    labels[retreat_zone] = np.where(labels[retreat_zone] == 1, 2, np.where(labels[retreat_zone] == 2, 1, labels[retreat_zone]))

    df["risk_level"] = labels

    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def write_csv(path: Path = OUTPUT_PATH, n: int = 700, seed: int = 42) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    generate(n=n, seed=seed).to_csv(path, index=False)
    print(f"Stratified dataset generated at {path.resolve()} ({n} rows)")


if __name__ == "__main__":
    write_csv()