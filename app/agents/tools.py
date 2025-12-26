"""
Agent tool functions (Strands @tool wrappers).

All tools return structured data for agent consumption.
Tools delegate to domain/data layers; no business logic here.
"""

import logging
from typing import Any

from strands import tool

from app.data.forecast_service import OfflineModeError, get_forecast_points
from app.data.station_matching import InvalidCoordinatesError, haversine_km, pick_nearest_point
from app.domain.irrigation_engine import compute_plan
from app.domain.models import ForecastPoint, ProfileInput
from app.utils.config import settings

logger = logging.getLogger(__name__)


@tool
def tool_get_forecast_points(date_str: str | None = None) -> list[dict[str, Any]]:
    """
    Fetch forecast points for a given date.

    Retrieves evaporation and weather forecast data from cache or API.
    Respects offline mode configuration.

    Args:
        date_str: Forecast date in YYYY-MM-DD format (defaults to today if None)

    Returns:
        List of ForecastPoint dictionaries with fields:
        - date: str (YYYY-MM-DD)
        - lat: float
        - lon: float
        - evap_mm: float (daily evaporation in mm)
        - temp_min: float | None
        - temp_max: float | None
        - name: str | None
        - geographic_area: str | None
    """
    try:
        points = get_forecast_points(date_str=date_str, offline_mode=settings.offline_mode)
        # Convert Pydantic models to dicts for JSON serialization
        return [point.model_dump(mode="json") for point in points]
    except OfflineModeError:
        error_msg = (
            f"Offline mode enabled: no cached forecast data for date {date_str}. "
            "Run once online to populate cache, or disable offline mode."
        )
        logger.error(error_msg)
        return [{"error": error_msg}]
    except Exception as e:
        error_msg = f"Failed to fetch forecast points: {str(e)}"
        logger.error(error_msg)
        return [{"error": error_msg}]


@tool
def tool_pick_nearest_point(
    user_lat: float, user_lon: float, points: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Select the nearest forecast point to user location.

    Uses Haversine distance calculation with deterministic tie-breaking.

    Args:
        user_lat: User latitude (must be between -90 and 90)
        user_lon: User longitude (must be between -180 and 180)
        points: List of ForecastPoint dictionaries (from tool_get_forecast_points)

    Returns:
        Dictionary with:
        - forecast_point: ForecastPoint dict (date, lat, lon, evap_mm, name, etc.)
        - distance_km: float (distance from user location in kilometers)
        - error: str (only if an error occurred)
    """
    if not points:
        return {"error": "Cannot select nearest point: points list is empty"}

    # Check for error in points
    if len(points) == 1 and "error" in points[0]:
        return {"error": points[0]["error"]}

    # Convert dicts to ForecastPoint models
    try:
        forecast_points = [ForecastPoint(**point) for point in points]
    except Exception as e:
        return {"error": f"Invalid forecast points data: {str(e)}"}

    try:
        nearest = pick_nearest_point(user_lat, user_lon, forecast_points)
        distance_km = haversine_km(user_lat, user_lon, nearest.lat, nearest.lon)
        return {
            "forecast_point": nearest.model_dump(mode="json"),
            "distance_km": round(distance_km, 2),
        }
    except InvalidCoordinatesError as e:
        error_msg = (
            f"Cannot select nearest point: all {e.total_points} point(s) "
            f"have invalid coordinates. Skipped {e.skipped_count} point(s)."
        )
        logger.error(error_msg)
        return {"error": error_msg}
    except ValueError as e:
        error_msg = f"Invalid coordinates: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@tool
def tool_compute_irrigation(
    profile: dict[str, Any], forecast_point: dict[str, Any]
) -> dict[str, Any]:
    """
    Compute irrigation plan from profile and forecast point.

    Uses the deterministic irrigation engine to calculate daily water needs.
    This is the ONLY way to get irrigation amounts - do not guess or calculate manually.

    Args:
        profile: ProfileInput dictionary with fields:
            - mode: "farm" or "plant"
            - lat: float
            - lon: float
            - For farm mode: area_m2 or area_dunam, crop_name, stage (optional)
            - For plant mode: pot_volume_liters or pot_diameter_cm, plant_profile_name
            - irrigation_method: str (optional, e.g., "drip", "sprinkler")
            - efficiency: float (optional, 0-1)
        forecast_point: ForecastPoint dictionary (from tool_pick_nearest_point)

    Returns:
        IrrigationPlan dictionary with fields:
        - date: str (YYYY-MM-DD)
        - mode: "farm" or "plant"
        - liters_per_day: float | None (farm mode)
        - liters_per_dunam: float | None (farm mode)
        - ml_per_day: float | None (plant mode)
        - pulses_per_day: int
        - inputs_used: dict
        - coefficient_value_used: float
        - coefficient_source: dict
        - warnings: list[str]
        - error: str (only if an error occurred)
    """
    # Check for error in forecast_point
    if "error" in forecast_point:
        return {"error": forecast_point["error"]}

    try:
        # Convert dicts to Pydantic models
        profile_model = ProfileInput(**profile)
        forecast_model = ForecastPoint(**forecast_point)

        # Compute plan using deterministic engine
        plan = compute_plan(profile_model, forecast_model)

        # Convert to dict for JSON serialization
        return plan.model_dump(mode="json")
    except ValueError as e:
        error_msg = f"Invalid inputs: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Computation failed: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
