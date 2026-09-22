"""Pytest fixtures.

Environment overrides MUST be set before any application import so that
``core.config.Settings`` and ``db.database.engine`` bind to a throwaway
database and model store that are fresh per test session.
"""

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="paths_test_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "test.db").replace("\\", "/")
os.environ["MODEL_STORE_DIR"] = os.path.join(_TMP, "model_store")
os.environ["JWT_SECRET"] = "pytest-secret-not-real"
os.environ["ENV"] = "testing"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def trained_store():
    """Train v1 into the isolated store before any inference/API test."""
    from model.trainer import train

    from core.config import settings

    result = train(settings.BACKEND_DATA_PATH)
    # Flush the module-level PredictionService so it binds to the trained v1.
    from model.predictor import service

    service.flush()
    return result


@pytest.fixture(scope="session")
def client():
    from api.app import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_headers(client):
    resp = client.post(
        "/login",
        json={"email": "admin@paths.io", "password": "admin123"},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def viewer_headers(client):
    resp = client.post(
        "/login",
        json={"email": "viewer@paths.io", "password": "viewer123"},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}