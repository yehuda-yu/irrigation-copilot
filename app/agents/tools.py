"""
Agent tool functions (Strands @tool wrappers).

All tools return structured data for agent consumption.
Tools delegate to domain/data layers; no business logic here.
"""

import datetime
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
def tool_get_forecast_points(date_str: str | None = None) -> dict[str, Any]:
    """
    Check availability of forecast data for a given date.

    Args:
        date_str: Forecast date in YYYY-MM-DD format (defaults to today if None)

    Returns:
        Summary dictionary:
        - date: str (the date used)
        - count: int (number of available forecast points)
        - areas: list (available geographic areas)
        - error: str (if any)
    """
    try:
        points = get_forecast_points(date_str=date_str, offline_mode=settings.offline_mode)
        areas = sorted(list(set(p.geographic_area for p in points if p.geographic_area)))

        # We don't return the full list to the agent to save tokens.
        # The agent should use tool_pick_nearest_point to find the right one.
        return {
            "date": date_str or datetime.now().date().isoformat(),
            "count": len(points),
            "available_areas": areas[:10],  # Show a sample of areas
            "message": "Data available. Now use tool_pick_nearest_point with your coordinates."
        }
    except OfflineModeError:
        error_msg = (
            f"Offline mode enabled: no cached forecast data for date {date_str}. "
            "Run once online to populate cache, or disable offline mode."
        )
        logger.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Failed to fetch forecast points: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@tool
def tool_pick_nearest_point(
    user_lat: float, user_lon: float, date_str: str | None = None
) -> dict[str, Any]:
    """
    Select the nearest forecast point to user location for a specific date.

    Args:
        user_lat: User latitude (must be between -90 and 90)
        user_lon: User longitude (must be between -180 and 180)
        date_str: Date for the forecast (defaults to today)

    Returns:
        Dictionary with:
        - forecast_point: ForecastPoint dict (date, lat, lon, evap_mm, name, etc.)
        - distance_km: float (distance from user location in kilometers)
        - error: str (only if an error occurred)
    """
    try:
        # Fetch points internally to avoid passing massive lists through LLM context
        points = get_forecast_points(date_str=date_str, offline_mode=settings.offline_mode)

        if not points:
            return {"error": f"No forecast points available for date {date_str}"}

        nearest = pick_nearest_point(user_lat, user_lon, points)
        distance_km = haversine_km(user_lat, user_lon, nearest.lat, nearest.lon)

        return {
            "forecast_point": nearest.model_dump(mode="json"),
            "distance_km": round(distance_km, 2),
        }
    except InvalidCoordinatesError as e:
        error_msg = f"No valid coordinates found among {e.total_points} points."
        logger.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Failed to pick nearest point: {str(e)}"
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
