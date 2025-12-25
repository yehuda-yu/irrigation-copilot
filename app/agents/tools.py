"""
Agent tool functions.

All tools return Pydantic models (structured outputs) for agent consumption.
Tools delegate to domain/data layers; no business logic here.
"""

from app.domain.models import ForecastPoint, IrrigationPlan, ProfileInput


def collect_profile() -> ProfileInput:
    """
    Collect user profile input (location, area, crop type, irrigation method).

    Returns:
        ProfileInput: User profile data
    """
    # TODO: Implement profile collection
    pass


def fetch_forecast(lat: float, lon: float) -> list[ForecastPoint]:
    """
    Fetch forecast data for given location.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        List of ForecastPoint objects
    """
    # TODO: Implement forecast fetching via data adapter
    pass


def pick_point(forecast_points: list[ForecastPoint], lat: float, lon: float) -> ForecastPoint:
    """
    Select appropriate forecast point for user location.

    Args:
        forecast_points: Available forecast points
        lat: User latitude
        lon: User longitude

    Returns:
        Selected ForecastPoint
    """
    # TODO: Implement point selection logic
    pass


def lookup_kc(crop_type: str) -> float:
    """
    Lookup Kc value from catalog.

    Args:
        crop_type: Crop or plant type identifier

    Returns:
        Kc coefficient value
    """
    # TODO: Implement Kc lookup from catalog
    pass


def compute(profile: ProfileInput, forecast: ForecastPoint, kc: float) -> IrrigationPlan:
    """
    Compute irrigation plan using domain engine.

    Args:
        profile: User profile
        forecast: Selected forecast point
        kc: Crop coefficient

    Returns:
        Computed IrrigationPlan
    """
    # TODO: Call domain engine compute function
    pass


def format_output(plan: IrrigationPlan) -> str:
    """
    Format irrigation plan into user-friendly text.

    Args:
        plan: Computed irrigation plan

    Returns:
        Formatted text output
    """
    # TODO: Implement formatting logic
    pass
