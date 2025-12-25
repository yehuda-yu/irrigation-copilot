"""Data adapters package."""

# Re-export main entry point for backwards compatibility
from app.data.forecast_service import (
    OfflineModeError,
    get_forecast_points,
)

__all__ = ["get_forecast_points", "OfflineModeError"]
