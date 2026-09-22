def test_login_success_admin(client):
    resp = client.post(
        "/login",
        json={"email": "admin@paths.io", "password": "admin123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "admin"
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_wrong_password(client):
    resp = client.post(
        "/login",
        json={"email": "admin@paths.io", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post(
        "/login",
        json={"email": "nobody@paths.io", "password": "admin123"},
    )
    assert resp.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_rejects_invalid_token(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401


def test_me_with_valid_token(client, admin_headers):
    resp = client.get("/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_viewer_cannot_coordinate(client, viewer_headers):
    payload = {
        "attendance": 90,
        "internal_marks": 85,
        "assignments": 88,
        "study_hours": 6,
        "backlog_count": 0,
        "stress_level": 3,
    }
    resp = client.post("/coordinate", json=payload, headers=viewer_headers)
    assert resp.status_code == 403


def test_no_token_cannot_coordinate(client):
    payload = {
        "attendance": 90,
        "internal_marks": 85,
        "assignments": 88,
        "study_hours": 6,
        "backlog_count": 0,
        "stress_level": 3,
    }
    resp = client.post("/coordinate", json=payload)
    assert resp.status_code == 401