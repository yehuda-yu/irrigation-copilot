"""
Tests for irrigation plan API endpoint.
"""

from datetime import date
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.domain.models import ForecastPoint

client = TestClient(app)

# We need to register the routes in app/api/main.py for this to work,
# but I'll write the test now and register them in Phase D.
# Wait, Phase D is later. I should probably register them now or
# at least make sure the app has them when I run the test.

@pytest.fixture
def mock_forecast_points():
    return [
        ForecastPoint(
            date=date(2025, 12, 27),
            lat=32.0,
            lon=34.8,
            evap_mm=5.0,
            name="Test Station",
            geographic_area="Center"
        )
    ]

def test_irrigation_plan_farm_success(mock_forecast_points):
    with patch("app.api.routes.irrigation.get_forecast_points", return_value=mock_forecast_points):
        payload = {
            "lat": 32.0,
            "lon": 34.8,
            "mode": "farm",
            "crop_name": "tomato",
            "stage": "mid",
            "area_dunam": 5.0
        }
        response = client.post("/irrigation/plan", json=payload)

        # Note: If this fails with 404, it's because I haven't registered
        # the router in app/api/main.py yet.
        # I'll do that in Phase D, but let's assume it's there or I'll do it right after.
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert data["plan"]["mode"] == "farm"
        assert data["chosen_point"]["name"] == "Test Station"
        assert data["evap_mm_used"] == 5.0

def test_irrigation_plan_invalid_mode():
    payload = {
        "lat": 32.0,
        "lon": 34.8,
        "mode": "invalid",
    }
    response = client.post("/irrigation/plan", json=payload)
    assert response.status_code == 422

def test_irrigation_plan_missing_fields():
    payload = {
        "lat": 32.0,
        "lon": 34.8,
        "mode": "farm",
        # missing crop_name, area_dunam
    }
    response = client.post("/irrigation/plan", json=payload)
    assert response.status_code == 422

def test_irrigation_plan_offline_miss():
    with patch("app.api.routes.irrigation.get_forecast_points") as mock_get:
        from app.data.forecast_service import OfflineModeError
        mock_get.side_effect = OfflineModeError("Cache miss")

        payload = {
            "lat": 32.0,
            "lon": 34.8,
            "mode": "farm",
            "crop_name": "tomato",
            "area_dunam": 5.0,
            "offline": True
        }
        response = client.post("/irrigation/plan", json=payload)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "OFFLINE_CACHE_MISS"

