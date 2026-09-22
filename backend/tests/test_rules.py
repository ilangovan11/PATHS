"""Unit tests for the deterministic safety-rule layer.

Rule priorities (must never change silently):
1. Critical risk override -> RETREAT
2. Low confidence gate    -> HOLD
3. Model prediction map   -> ADVANCE / HOLD / RETREAT
"""

from engine.paths_logic import evaluate_rules


def test_low_attendance_critical_override():
    action, reason, rules = evaluate_rules("ADVANCE", 0.99, [40, 80, 80, 5, 0, 3])
    assert action == "RETREAT"
    assert "Critical risk" in reason
    assert rules[0]["rule"] == "critical_risk_override"
    assert rules[0]["triggered"] is True


def test_backlog_stress_critical_override():
    action, reason, rules = evaluate_rules("ADVANCE", 0.99, [80, 80, 80, 4, 6, 9])
    assert action == "RETREAT"
    assert rules[0]["triggered"] is True


def test_critical_override_not_triggered_when_condition_false():
    action, _, rules = evaluate_rules("ADVANCE", 0.99, [60, 80, 80, 5, 3, 7])
    assert rules[0]["triggered"] is False
    assert action == "ADVANCE"


def test_low_confidence_gate_returns_hold():
    action, reason, rules = evaluate_rules("RETREAT", 0.50, [80, 80, 80, 5, 0, 3])
    assert action == "HOLD"
    assert "Low confidence" in reason
    assert rules[1]["rule"] == "low_confidence_gate"
    assert rules[1]["triggered"] is True


def test_prediction_map_advance():
    action, _, rules = evaluate_rules("ADVANCE", 0.9, [80, 80, 80, 5, 0, 3])
    assert action == "ADVANCE"
    assert any(r["rule"] == "model_prediction_map" for r in rules)


def test_prediction_map_hold():
    action, _, _ = evaluate_rules("HOLD", 0.9, [80, 80, 80, 5, 1, 4])
    assert action == "HOLD"


def test_prediction_map_retreat():
    action, _, _ = evaluate_rules("RETREAT", 0.9, [80, 80, 80, 5, 1, 4])
    assert action == "RETREAT"


def test_all_rules_recorded():
    _, _, rules = evaluate_rules("ADVANCE", 0.9, [80, 80, 80, 5, 0, 3])
    assert [r["rule"] for r in rules] == [
        "critical_risk_override",
        "low_confidence_gate",
        "model_prediction_map",
    ]