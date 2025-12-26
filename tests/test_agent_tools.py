"""
Offline tests for agent tools.

Tests tool wrappers with synthetic data (no network calls, no OpenAI API).
These tests verify the tool functions work correctly when called directly.
"""

import pytest

# Skip these tests if strands is not available
pytest.importorskip("strands")


def test_tool_pick_nearest_point_valid():
    """Test tool_pick_nearest_point with valid inputs."""
    from app.agents.tools import tool_pick_nearest_point

    points = [
        {
            "date": "2025-01-15",
            "lat": 32.0,
            "lon": 34.0,
            "evap_mm": 5.0,
            "name": "Near Station",
        },
        {
            "date": "2025-01-15",
            "lat": 33.0,
            "lon": 35.0,
            "evap_mm": 6.0,
            "name": "Far Station",
        },
    ]

    result = tool_pick_nearest_point(32.1, 34.1, points)

    assert "forecast_point" in result
    assert "distance_km" in result
    assert result["forecast_point"]["name"] == "Near Station"
    assert result["distance_km"] > 0
    assert result["distance_km"] < 100  # Should be close


def test_tool_pick_nearest_point_empty_list():
    """Test tool_pick_nearest_point returns error with empty list."""
    from app.agents.tools import tool_pick_nearest_point

    result = tool_pick_nearest_point(32.0, 34.0, [])
    assert "error" in result
    assert "empty" in result["error"]


def test_tool_pick_nearest_point_invalid_coords():
    """Test tool_pick_nearest_point returns error with invalid user coordinates."""
    from app.agents.tools import tool_pick_nearest_point

    points = [
        {
            "date": "2025-01-15",
            "lat": 32.0,
            "lon": 34.0,
            "evap_mm": 5.0,
        }
    ]

    # Invalid latitude
    result = tool_pick_nearest_point(100.0, 34.0, points)
    assert "error" in result

    # Invalid longitude
    result = tool_pick_nearest_point(32.0, 200.0, points)
    assert "error" in result


def test_tool_compute_irrigation_farm_mode():
    """Test tool_compute_irrigation with farm mode profile."""
    from app.agents.tools import tool_compute_irrigation

    profile = {
        "mode": "farm",
        "lat": 32.0,
        "lon": 34.0,
        "area_m2": 100.0,
        "crop_name": "tomato",
        "stage": "mid",
    }
    forecast_point = {
        "date": "2025-01-15",
        "lat": 32.0,
        "lon": 34.0,
        "evap_mm": 5.0,
    }

    result = tool_compute_irrigation(profile, forecast_point)

    assert "error" not in result
    assert "mode" in result
    assert result["mode"] == "farm"
    assert "liters_per_day" in result
    assert result["liters_per_day"] is not None
    assert result["liters_per_day"] > 0
    assert "ml_per_day" in result
    assert result["ml_per_day"] is None
    assert "pulses_per_day" in result
    assert "coefficient_value_used" in result
    assert "warnings" in result


def test_tool_compute_irrigation_plant_mode():
    """Test tool_compute_irrigation with plant mode profile."""
    from app.agents.tools import tool_compute_irrigation

    profile = {
        "mode": "plant",
        "lat": 32.0,
        "lon": 34.0,
        "pot_volume_liters": 5.0,
        "plant_profile_name": "tomato_plant",
    }
    forecast_point = {
        "date": "2025-01-15",
        "lat": 32.0,
        "lon": 34.0,
        "evap_mm": 5.0,
    }

    result = tool_compute_irrigation(profile, forecast_point)

    assert "error" not in result
    assert "mode" in result
    assert result["mode"] == "plant"
    assert "ml_per_day" in result
    assert result["ml_per_day"] is not None
    assert result["ml_per_day"] > 0
    assert "liters_per_day" in result
    assert result["liters_per_day"] is None


def test_tool_compute_irrigation_invalid_crop():
    """Test tool_compute_irrigation returns error with unknown crop."""
    from app.agents.tools import tool_compute_irrigation

    profile = {
        "mode": "farm",
        "lat": 32.0,
        "lon": 34.0,
        "area_m2": 100.0,
        "crop_name": "unknown_crop_xyz",
        "stage": "mid",
    }
    forecast_point = {
        "date": "2025-01-15",
        "lat": 32.0,
        "lon": 34.0,
        "evap_mm": 5.0,
    }

    result = tool_compute_irrigation(profile, forecast_point)
    assert "error" in result
    assert "not supported" in result["error"] or "Invalid" in result["error"]


def test_tool_compute_irrigation_invalid_profile():
    """Test tool_compute_irrigation returns error with invalid profile."""
    from app.agents.tools import tool_compute_irrigation

    profile = {
        "mode": "farm",
        "lat": 32.0,
        "lon": 34.0,
        # Missing required fields
    }
    forecast_point = {
        "date": "2025-01-15",
        "lat": 32.0,
        "lon": 34.0,
        "evap_mm": 5.0,
    }

    result = tool_compute_irrigation(profile, forecast_point)
    assert "error" in result


def test_tool_compute_irrigation_with_error_in_forecast():
    """Test tool_compute_irrigation propagates error from forecast_point."""
    from app.agents.tools import tool_compute_irrigation

    profile = {
        "mode": "farm",
        "lat": 32.0,
        "lon": 34.0,
        "area_m2": 100.0,
        "crop_name": "tomato",
    }
    forecast_point = {
        "error": "Some upstream error",
    }

    result = tool_compute_irrigation(profile, forecast_point)
    assert "error" in result
    assert "upstream" in result["error"]
