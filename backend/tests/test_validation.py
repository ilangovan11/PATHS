import pytest

VALID = {
    "attendance": 90,
    "internal_marks": 85,
    "assignments": 88,
    "study_hours": 6.0,
    "backlog_count": 0,
    "stress_level": 3,
}

INVALID_CASES = [
    ("attendance_above_range", {**VALID, "attendance": 101}),
    ("attendance_below_range", {**VALID, "attendance": -1}),
    ("marks_above_range", {**VALID, "internal_marks": 101}),
    ("assignments_above_range", {**VALID, "assignments": 240}),
    ("study_hours_above_range", {**VALID, "study_hours": 17}),
    ("study_hours_negative", {**VALID, "study_hours": -0.5}),
    ("backlog_above_range", {**VALID, "backlog_count": 21}),
    ("backlog_negative", {**VALID, "backlog_count": -2}),
    ("stress_below_range", {**VALID, "stress_level": 0}),
    ("stress_above_range", {**VALID, "stress_level": 11}),
]


@pytest.mark.parametrize("case_name,payload", INVALID_CASES, ids=[c[0] for c in INVALID_CASES])
def test_coordinate_rejects_out_of_range(client, admin_headers, case_name, payload):
    resp = client.post("/coordinate", json=payload, headers=admin_headers)
    assert resp.status_code == 422, case_name


def test_coordinate_rejects_out_of_range_marks(client, admin_headers):
    resp = client.post(
        "/coordinate",
        json={**VALID, "internal_marks": 101},
        headers=admin_headers,
    )
    assert resp.status_code == 422


def test_coordinate_rejects_non_numeric(client, admin_headers):
    resp = client.post(
        "/coordinate",
        json={**VALID, "attendance": "ninety"},
        headers=admin_headers,
    )
    assert resp.status_code == 422