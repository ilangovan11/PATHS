"""Dataset quality tests for the v2 synthetic generator.

These protect the invariant that fixed the perfect-student bug: labels must be
coherent with the documented decision semantics (good indicators -> ADVANCE,
bad indicators -> RETREAT), the full valid input domain must be covered so the
model never has to extrapolate, and generation must be deterministic.
"""

import pandas as pd
import pytest


def test_generation_is_deterministic():
    from data.raw.generate_data import generate

    a = generate(n=700, seed=42)
    b = generate(n=700, seed=42)
    pd.testing.assert_frame_equal(a, b)


def test_dataset_schema_and_ranges():
    from data.raw.generate_data import generate

    df = generate(n=700, seed=42)
    assert list(df.columns) == [
        "attendance",
        "internal_marks",
        "assignments",
        "study_hours",
        "backlog_count",
        "stress_level",
        "risk_level",
    ]
    assert df["attendance"].between(0, 100).all()
    assert df["internal_marks"].between(0, 100).all()
    assert df["assignments"].between(0, 100).all()
    assert df["study_hours"].between(0.5, 16.0).all()
    assert df["backlog_count"].between(0, 20).all()
    assert df["stress_level"].between(1, 10).all()
    assert df["risk_level"].isin([0, 1, 2]).all()
    assert not df.duplicated().any()


def test_classes_are_reasonably_balanced():
    from data.raw.generate_data import generate

    df = generate(n=700, seed=42)
    proportions = df["risk_level"].value_counts(normalize=True).sort_index()
    for prop in proportions:
        assert 0.15 <= prop <= 0.55


def test_full_input_domain_is_covered():
    """The previous dataset capped at attendance/marks ~95, which forced the
    model to extrapolate for 'perfect' inputs. The v2 data must cover the
    top and bottom of the valid ranges."""
    from data.raw.generate_data import generate

    df = generate(n=700, seed=42)
    assert (df["attendance"] >= 95).any()
    assert (df["internal_marks"] >= 90).any()
    assert (df["assignments"] >= 90).any()
    assert (df["study_hours"] >= 12.0).any()
    assert (df["backlog_count"] <= 1).any() & (df["stress_level"] <= 3).any()


def test_no_gross_label_contradictions():
    """A student with excellent indicators across the board must not be
    labeled RETREAT (this exact contradiction existed in v1 data and caused
    the perfect-student HOLD bug)."""
    from data.raw.generate_data import generate

    df = generate(n=700, seed=42)
    excellent = df[
        (df["attendance"] >= 90)
        & (df["internal_marks"] >= 85)
        & (df["assignments"] >= 85)
        & (df["backlog_count"] <= 1)
        & (df["stress_level"] <= 3)
    ]
    assert len(excellent) >= 3  # region is actually populated
    assert (excellent["risk_level"] == 0).all(), "excellent rows mislabeled!"

    terrible = df[
        (df["attendance"] <= 45)
        & (df["internal_marks"] <= 40)
        & (df["backlog_count"] >= 6)
        & (df["stress_level"] >= 7)
    ]
    assert len(terrible) >= 3
    assert (terrible["risk_level"] == 2).all(), "terrible rows mislabeled!"


def test_perfect_student_maps_to_advance_label():
    """100/100/100 with low backlog and stress must be labeled ADVANCE (0)."""
    from data.raw.generate_data import _latent_score

    row = pd.DataFrame(
        {
            "attendance": [100],
            "internal_marks": [100],
            "assignments": [100],
            "study_hours": [8.0],
            "backlog_count": [0],
            "stress_level": [1],
        }
    )
    score = _latent_score(row)[0]
    assert score >= 0.50


@pytest.mark.parametrize("seed", [7, 1234])
def test_generation_robust_across_seeds(seed):
    from data.raw.generate_data import generate

    df = generate(n=700, seed=seed)
    assert df["risk_level"].isin([0, 1, 2]).all()
    proportions = df["risk_level"].value_counts(normalize=True).sort_index()
    for prop in proportions:
        assert 0.12 <= prop <= 0.60