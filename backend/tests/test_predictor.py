"""Predictor + registry + health unit/integration tests."""

from model.predictor import service as prediction_service
from model.config import CLASS_NAMES, FEATURE_ORDER

VALID_LOW_RISK = [85, 78, 80, 5.0, 0, 3]
VALID_HIGH_RISK = [45, 70, 65, 3.5, 6, 9]


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "alive"
    assert body["database"] == "ok"
    assert body["active_model"] is not None


def test_version_endpoint(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    assert resp.json()["version"].startswith("2.")


def test_predictor_returns_valid_class():
    result = prediction_service.predict(VALID_LOW_RISK)
    assert result["prediction_class"] in CLASS_NAMES.values()
    assert 0.0 <= result["confidence"] <= 1.0
    assert list(result["probabilities"].keys()) == [str(c) for c in CLASS_NAMES]
    assert result["model_version"].startswith("v")


def test_predictor_probabilities_sum_to_one():
    result = prediction_service.predict(VALID_LOW_RISK)
    total = sum(float(p) for p in result["probabilities"].values())
    assert abs(total - 1.0) < 1e-6


def test_feature_importances_from_actual_model():
    importances = prediction_service.feature_importances()
    assert len(importances) == len(FEATURE_ORDER)
    names = [i["feature"] for i in importances]
    assert names == FEATURE_ORDER
    total = sum(i["importance"] for i in importances)
    assert abs(total - 1.0) < 0.02


def test_registry_versions_consistent():
    from core.config import settings
    from model import registry

    exported = registry.load_registry(settings.MODEL_STORE_DIR)
    from model.predictor import service

    assert exported["active_model"] == service.get()["version"]