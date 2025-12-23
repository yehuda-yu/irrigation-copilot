"""
MoAG forecast data parser.

Parses raw MoAG API responses into normalized ForecastPoint models.
Handles data validation and normalization.
"""

from app.domain.models import ForecastPoint


def parse_forecast_response(raw_data: dict) -> list[ForecastPoint]:
    """
    Parse raw MoAG API response into ForecastPoint list.
    
    Args:
        raw_data: Raw API response dictionary
    
    Returns:
        List of normalized ForecastPoint objects
    
    Raises:
        ValueError: If data format is invalid
    """
    # TODO: Implement parsing logic
    pass


def normalize_evap(evap_value: float, unit: str) -> float:
    """
    Normalize evaporation value to mm/day.
    
    Args:
        evap_value: Evaporation value
        unit: Source unit (e.g., 'mm', 'cm')
    
    Returns:
        Normalized value in mm/day
    """
    # TODO: Implement unit normalization
    pass

