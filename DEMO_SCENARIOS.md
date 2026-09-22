# PATHS — Demo Scenarios (live-run results)

All four scenarios below were executed against the real application (admin JWT, active model `v1`) on 2026-09-22 and the responses below are the **actual recorded outputs** — nothing is paraphrased.

---

## Scenario A — Healthy student → ADVANCE

**Input**

```json
{"attendance": 90, "internal_marks": 85, "assignments": 88, "study_hours": 6, "backlog_count": 0, "stress_level": 3}
```

**Response** (`POST /coordinate`, 200)

```json
{
  "prediction": "ADVANCE",
  "action": "ADVANCE",
  "confidence": 0.9991,
  "reason": "Performance indicators are stable",
  "model_version": "v1",
  "probabilities": {"0": 0.9991, "1": 0.0009, "2": 0.0},
  "rules_checked": [
    {"rule": "critical_risk_override", "condition": "attendance < 50 OR (backlogs >= 5 AND stress >= 8)", "triggered": false},
    {"rule": "low_confidence_gate", "condition": "confidence < 0.6", "triggered": false},
    {"rule": "model_prediction_map", "condition": "model prediction is ADVANCE", "triggered": true}
  ],
  "trace": [
    "Input validated against documented feature ranges.",
    "Features scaled using the active model's StandardScaler (model v1).",
    "Model prediction: ADVANCE (confidence 0.999).",
    "Safety rules evaluated.",
    "Final action: ADVANCE."
  ]
}
```

No rule fired; the action came directly from the model's class 0.

---

## Scenario B — Critical risk → RETREAT override

**Input**

```json
{"attendance": 40, "internal_marks": 60, "assignments": 55, "study_hours": 2, "backlog_count": 6, "stress_level": 9}
```

**Response** (200)

```json
{
  "prediction": "RETREAT",
  "action": "RETREAT",
  "confidence": 0.95,
  "reason": "Critical risk detected by rule override",
  "model_version": "v1",
  "probabilities": {"0": 0.0, "1": 0.05, "2": 0.95},
  "rules_checked": [
    {"rule": "critical_risk_override", "condition": "attendance < 50 OR (backlogs >= 5 AND stress >= 8)", "triggered": true}
  ],
  "trace": [
    "Input validated against documented feature ranges.",
    "Features scaled using the active model's StandardScaler (model v1).",
    "Model prediction: RETREAT (confidence 0.95).",
    "Safety rules evaluated.",
    "Final action: RETREAT."
  ]
}
```

The critical-risk rule (`attendance < 50` **and** `backlogs ≥ 5`, `stress ≥ 8`) short-circuits evaluation — no further rules are checked.

---

## Scenario C — Low confidence (no override) → HOLD

**Input**

```json
{"attendance": 50, "internal_marks": 70, "assignments": 65, "study_hours": 3, "backlog_count": 4, "stress_level": 7}
```

**Response** (200)

```json
{
  "prediction": "HOLD",
  "action": "HOLD",
  "confidence": 0.57,
  "reason": "Low confidence in prediction",
  "model_version": "v1",
  "probabilities": {"0": 0.0, "1": 0.57, "2": 0.43},
  "rules_checked": [
    {"rule": "critical_risk_override", "condition": "attendance < 50 OR (backlogs >= 5 AND stress >= 8)", "triggered": false},
    {"rule": "low_confidence_gate", "condition": "confidence < 0.6", "triggered": true}
  ],
  "trace": [
    "Input validated against documented feature ranges.",
    "Features scaled using the active model's StandardScaler (model v1).",
    "Model prediction: HOLD (confidence 0.57).",
    "Safety rules evaluated.",
    "Final action: HOLD."
  ]
}
```

The model itself was unsure (0.57 / 0.43 split between HOLD and RETREAT), so the confidence gate forced a HOLD regardless of the raw class.

---

## Scenario D — Invalid input → HTTP 422

**Input** (stress_level out of range)

```json
{"attendance": 50, "internal_marks": 70, "assignments": 65, "study_hours": 3, "backlog_count": 4, "stress_level": 11}
```

**Response** (422)

```json
{
  "detail": "Validation error",
  "errors": [
    {
      "loc": ["body", "stress_level"],
      "msg": "ensure this value is less than or equal to 10",
      "type": "value_error.number.not_le",
      "ctx": {"limit_value": 10}
    }
  ]
}
```

The decision engine is never invoked — Pydantic rejects the request at the API boundary. This closes the baseline defect where out-of-range rows were silently extrapolated and persisted.

---

## Reproduction

Start the stack (see `README.md` §6/§7), authenticate with the admin account, and `POST` each input body to `/coordinate` (or use the Coordinate page in the dashboard). Expected results are exactly as recorded above for active model `v1`.