"""
Station matching logic.

Matches user location (lat/lon) to nearest forecast point or weather station.
Used by pick_point tool to select appropriate forecast data.
"""

from app.domain.models import ForecastPoint


def find_nearest_point(
    forecast_points: list[ForecastPoint],
    lat: float,
    lon: float,
) -> ForecastPoint:
    """
    Find nearest forecast point to user location.
    
    Args:
        forecast_points: Available forecast points
        lat: User latitude
        lon: User longitude
    
    Returns:
        Nearest ForecastPoint
    
    Raises:
        ValueError: If no forecast points provided
    """
    # TODO: Implement distance calculation and selection
    pass


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates (Haversine formula).
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
    
    Returns:
        Distance in kilometers
    """
    # TODO: Implement Haversine distance calculation
    pass

