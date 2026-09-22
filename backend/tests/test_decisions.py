"""Integration tests: coordinate endpoint, persistence, analytics."""

HEALTHY = {
    "attendance": 90,
    "internal_marks": 85,
    "assignments": 88,
    "study_hours": 6.0,
    "backlog_count": 0,
    "stress_level": 3,
}


def test_coordinate_healthy_student(client, admin_headers):
    resp = client.post("/coordinate", json=HEALTHY, headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["action"] in ("ADVANCE", "HOLD", "RETREAT")
    assert body["prediction"] in ("ADVANCE", "HOLD", "RETREAT")
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["model_version"].startswith("v")
    assert isinstance(body["reason"], str) and body["reason"]
    assert body["trace"][0].startswith("Input validated")
    assert body["trace"][-1].startswith("Final action")
    assert len(body["rules_checked"]) == 3
    assert len(body["feature_importances"]) == 6
    for prob in body["probabilities"].values():
        assert 0.0 <= float(prob) <= 1.0


def test_coordinate_critical_override(client, admin_headers):
    resp = client.post(
        "/coordinate",
        json={**HEALTHY, "attendance": 40, "backlog_count": 6, "stress_level": 9},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "RETREAT"


def test_decisions_persisted_with_timestamps_and_version(client, admin_headers):
    client.post("/coordinate", json=HEALTHY, headers=admin_headers)

    from db.models import DecisionLog

    from db.database import SessionLocal

    db = SessionLocal()
    try:
        rows = db.query(DecisionLog).all()
        assert len(rows) >= 1
        row = rows[-1]
        assert row.created_at is not None
        assert row.model_version is not None
        assert row.decision_trace is not None
        assert row.triggered_by == "admin@paths.io"
        assert row.prediction in ("ADVANCE", "HOLD", "RETREAT")
        assert row.action in ("ADVANCE", "HOLD", "RETREAT")
    finally:
        db.close()


def test_analytics_summary_counts(client, admin_headers):
    client.post("/coordinate", json=HEALTHY, headers=admin_headers)
    resp = client.get("/analytics/summary", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_decisions"] == body["advance"] + body["hold"] + body["retreat"]
    assert body["total_decisions"] >= 1


def test_analytics_recent_rows(client, admin_headers):
    client.post("/coordinate", json=HEALTHY, headers=admin_headers)
    resp = client.get("/analytics/recent?limit=5", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 1
    assert rows[0]["created_at"] is not None
    assert rows[0]["model_version"] is not None


def test_analytics_accessible_to_viewer(client, viewer_headers):
    assert client.get("/analytics/summary", headers=viewer_headers).status_code == 200
    assert client.get("/analytics/confidence", headers=viewer_headers).status_code == 200
    assert client.get("/analytics/recent", headers=viewer_headers).status_code == 200