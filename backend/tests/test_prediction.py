"""
Pytest integration and unit tests for prediction and health endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.inference import model_service
from app.core.config import settings


@pytest.fixture(scope="session", autouse=True)
def load_test_model():
    """Ensure model is loaded before running tests."""
    if not model_service.is_loaded():
        model_service.load_model(settings.MODEL_PATH)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    """Test GET /health returns 200 and model_loaded status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True


def test_predict_valid_payload(client):
    """Test POST /predict with full feature set returns 200 and predicted_price."""
    payload = {
        "location": "mumbai",
        "locality": "Andheri West",
        "location_raw": "Andheri West, Mumbai",
        "transaction": "Resale",
        "furnishing": "Semi-Furnished",
        "facing": "East",
        "overlooking": "Garden/Park",
        "ownership": "Freehold",
        "carpet_area": 850.0,
        "super_area": 1100.0,
        "bathroom": 2.0,
        "balcony": 1.0,
        "parking_count": 1.0,
        "floor_number": 5.0,
        "building_height": 15.0,
    }

    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_price" in data
    assert isinstance(data["predicted_price"], (int, float))
    assert data["predicted_price"] > 0
    assert "formatted_price" in data


def test_predict_minimal_payload(client):
    """Test POST /predict with only required fields and missing/None optional fields."""
    payload = {
        "location": "pune",
        "transaction": "New Property",
        "bathroom": 1.0,
    }

    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_price" in data
    assert data["predicted_price"] >= 0


def test_predict_invalid_payload_missing_required(client):
    """Test POST /predict with missing required field returns 422."""
    payload = {
        "locality": "Whitefield",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
