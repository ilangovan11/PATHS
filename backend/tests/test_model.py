"""Model lifecycle integration tests against the isolated store."""


def test_model_status_reflects_trained_model(client, admin_headers):
    resp = client.get("/model/status", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["active_model"] is not None
    assert body["model_type"] == "RandomForestClassifier"
    assert body["features"] == [
        "attendance",
        "internal_marks",
        "assignments",
        "study_hours",
        "backlog_count",
        "stress_level",
    ]
    assert body["metrics"]["accuracy"] > 0.5
    assert body["metrics"]["f1_macro"] > 0.5
    assert len(body["metrics"]["feature_importances"]) == 6
    assert len(body["history"]) >= 1
    assert body["history"][0]["active"] is True


def test_model_versions(client, admin_headers):
    resp = client.get("/model/versions", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["active_model"] is not None
    assert len(body["history"]) >= 1


def test_retrain_registers_new_version(client, admin_headers):
    before = client.get("/model/versions", headers=admin_headers).json()
    before_count = len(before["history"])

    resp = client.post("/model/retrain", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["version"].startswith("v")
    assert body["metrics"]["accuracy"] > 0.5
    assert body["metrics"]["f1_macro"] > 0.5

    after = client.get("/model/versions", headers=admin_headers).json()
    assert len(after["history"]) == before_count + 1
    assert after["active_model"] == body["active_model"]


def test_activate_unknown_version_returns_404(client, admin_headers):
    resp = client.post(
        "/model/activate",
        json={"version": "v999"},
        headers=admin_headers,
    )
    assert resp.status_code == 404


def test_model_status_is_readable_by_viewer(client, viewer_headers):
    resp = client.get("/model/status", headers=viewer_headers)
    assert resp.status_code == 200
    assert resp.json()["active_model"] is not None


def test_retrain_requires_admin(client, viewer_headers):
    resp = client.post("/model/retrain", headers=viewer_headers)
    assert resp.status_code == 403


def test_activate_requires_admin(client, viewer_headers):
    resp = client.post(
        "/model/activate",
        json={"version": "v1"},
        headers=viewer_headers,
    )
    assert resp.status_code == 403