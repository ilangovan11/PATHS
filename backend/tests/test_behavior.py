"""Behavioral tests for the ML + decision pipeline.

These encode the documented expectations that were violated by the v1
dataset/model (perfect students coming back HOLD). They run against the real
trained model through the actual decision pipeline.

Expectations are semantic, not hardcoded: excellent profiles must ADVANCE,
high-risk profiles must RETREAT, and genuinely borderline profiles must not
silently pass as ADVANCE.
"""

import pytest

from engine.decision import coordinate
from engine.paths_logic import evaluate_rules
from model.predictor import service as prediction_service

ORDER = {"ADVANCE": 0, "HOLD": 1, "RETREAT": 2}


def decision_of(features):
    return coordinate(features)


@pytest.mark.parametrize(
    "profile",
    [
        [100, 100, 100, 6, 0, 1],
        [100, 100, 100, 8, 0, 1],
        [100, 100, 100, 12, 0, 1],
        [100, 100, 100, 16, 0, 1],
        [98, 95, 98, 7, 0, 1],
        [96, 94, 96, 10, 0, 2],
        [95, 90, 95, 7, 0, 2],
    ],
    ids=lambda p: f"att{p[0]}_m{p[1]}_a{p[2]}_s{p[3]}",
)
def test_excellent_student_is_advance(profile):
    result = decision_of(profile)
    assert result["action"] == "ADVANCE", (
        f"Excellent student {profile} returned {result['action']} "
        f"(confidence {result['confidence']}, probs {result['probabilities']})"
    )


@pytest.mark.parametrize(
    "profile",
    [
        [88, 84, 84, 6, 0, 3],
        [90, 85, 88, 6, 0, 3],
        [85, 80, 85, 5, 1, 4],
    ],
    ids=lambda p: f"att{p[0]}_m{p[1]}",
)
def test_healthy_student_is_advance(profile):
    result = decision_of(profile)
    assert result["action"] == "ADVANCE"


@pytest.mark.parametrize(
    "profile",
    [
        [70, 65, 65, 4, 3, 6],
        [68, 62, 62, 3.5, 2, 6],
        [55, 50, 48, 2.5, 4, 7],
    ],
    ids=lambda p: f"att{p[0]}_m{p[1]}",
)
def test_borderline_student_is_not_advance(profile):
    """Genuinely mixed profiles must not sail through as ADVANCE."""
    result = decision_of(profile)
    assert result["action"] in ("HOLD", "RETREAT")


def test_high_risk_student_is_retreat():
    result = decision_of([45, 50, 40, 1, 6, 9])
    assert result["action"] == "RETREAT"


def test_model_led_retreat_without_rule_override():
    """A profile the model itself marks high-risk (no rule override, no low
    confidence) must end up RETREAT through the model-prediction map."""
    profile = [55, 40, 38, 2.5, 4, 7]
    prediction = prediction_service.predict(profile)
    assert prediction["prediction_class"] == "RETREAT"
    assert prediction["confidence"] >= 0.6
    action, _, rules = evaluate_rules(
        prediction["prediction_class"], prediction["confidence"], profile
    )
    assert rules[0]["triggered"] is False
    assert action == "RETREAT"


def test_critical_rule_override_retreats():
    result = decision_of([40, 80, 80, 5, 0, 3])
    assert result["action"] == "RETREAT"
    critical = [r for r in result["rules_checked"] if r["rule"] == "critical_risk_override"]
    assert critical and critical[0]["triggered"] is True


def test_low_confidence_gate_is_consistent():
    """If the critical rule is not triggered but model confidence is below the
    0.6 gate, the decision must be HOLD regardless of the model prediction."""
    profile = [60, 42, 40, 2, 5, 7]
    prediction = prediction_service.predict(profile)
    action, reason, rules = evaluate_rules(
        prediction["prediction_class"], prediction["confidence"], profile
    )
    if not rules[0]["triggered"] and prediction["confidence"] < 0.6:
        assert action == "HOLD"
        assert "Low confidence" in reason


def test_decision_is_consistent_with_prediction_or_override():
    """The decision must either match the model prediction or be a documented
    rule override (critical risk or low confidence)."""
    for profile in [
        [100, 100, 100, 8, 0, 1],
        [75, 70, 68, 4, 2, 5],
        [50, 45, 40, 2, 5, 7],
        [40, 80, 80, 5, 0, 3],
    ]:
        result = decision_of(profile)
        overrides = {r["rule"] for r in result["rules_checked"] if r["triggered"]}
        consistent = result["action"] == result["prediction"] or bool(overrides)
        assert consistent, f"decision {result['action']} unexplained for {profile}"


def test_quality_gradient_is_monotonic_at_model_level():
    """As each consecutive profile in the gradient degrades overall quality,
    the model's predicted risk class must never jump to a strictly less risky
    class. This is a behavioral sanity check on the decision boundary."""
    gradient = [
        [95, 92, 90, 8, 0, 2],
        [88, 84, 84, 6, 0, 3],
        [78, 72, 72, 4.5, 1, 4],
        [68, 62, 62, 3.5, 2, 6],
        [55, 50, 48, 2.5, 4, 7],
        [40, 38, 35, 1.5, 6, 9],
        [25, 25, 25, 1, 9, 10],
    ]
    prev = -1
    for profile in gradient:
        prediction = prediction_service.predict(profile)
        rank = ORDER[prediction["prediction_class"]]
        assert rank >= prev, (
            f"risk regressed from rank {prev} to {rank} at profile {profile}"
        )
        prev = rank

    assert ORDER[decision_of(gradient[0])["action"]] == 0
    assert ORDER[decision_of(gradient[-1])["action"]] == 2


def test_model_version_consistent_across_calls():
    r1 = decision_of([100, 100, 100, 8, 0, 1])
    r2 = decision_of([70, 65, 65, 4, 3, 6])
    assert r1["model_version"] == r2["model_version"]
    assert r1["model_version"] == prediction_service.get()["version"]


def test_probabilities_cover_all_classes_and_sum_to_one():
    result = decision_of([100, 100, 100, 8, 0, 1])
    probs = result["probabilities"]
    assert set(probs) == {"0", "1", "2"}
    assert abs(sum(float(p) for p in probs.values()) - 1.0) < 1e-6
    assert result["class_names"] == {"0": "ADVANCE", "1": "HOLD", "2": "RETREAT"}