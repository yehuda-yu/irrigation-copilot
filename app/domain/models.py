"""
Domain models (Pydantic schemas).

API and agent contract models for irrigation planning.
All structured outputs from tools/API use these models.
"""

from datetime import date
from pydantic import BaseModel, Field


class ProfileInput(BaseModel):
    """User profile input for irrigation planning."""

    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    area_m2: float | None = Field(None, description="Area in square meters (farm mode)")
    pot_size_liters: float | None = Field(None, description="Pot size in liters (home mode)")
    crop_type: str = Field(..., description="Crop or plant type identifier")
    irrigation_method: str = Field(..., description="Irrigation method (e.g., 'drip', 'sprinkler')")
    efficiency: float = Field(0.8, ge=0.0, le=1.0, description="Irrigation system efficiency")


class ForecastPoint(BaseModel):
    """Normalized forecast data point."""

    date: date = Field(..., description="Forecast date")
    lat: float = Field(..., description="Point latitude")
    lon: float = Field(..., description="Point longitude")
    evap_mm: float = Field(..., description="Daily evaporation in mm")
    temp_min: float | None = Field(None, description="Minimum temperature (°C)")
    temp_max: float | None = Field(None, description="Maximum temperature (°C)")
    name: str | None = Field(None, description="Station/point name")
    area: str | None = Field(None, description="Geographic area identifier")


class IrrigationPlan(BaseModel):
    """Computed irrigation plan output."""

    date: date = Field(..., description="Plan date")
    irrigation_mm: float = Field(..., description="Recommended irrigation depth in mm/day")
    irrigation_liters: float = Field(..., description="Recommended irrigation volume in liters")
    irrigation_liters_per_dunam: float | None = Field(None, description="Liters per dunam (farm mode)")
    irrigation_ml: float | None = Field(None, description="Milliliters per day (home mode)")
    schedule: str | None = Field(None, description="Recommended schedule/pulse timing")
    card_text: str | None = Field(None, description="Shareable card text (home mode)")

