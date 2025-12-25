"""
Domain models (Pydantic schemas).

API and agent contract models for irrigation planning.
All structured outputs from tools/API use these models.
"""

import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ProfileInput(BaseModel):
    """User profile input for irrigation planning."""

    mode: Literal["farm", "plant"] = Field(..., description="Mode: 'farm' or 'plant'")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")

    # Farm mode fields
    area_m2: float | None = Field(None, description="Area in square meters (farm mode)")
    area_dunam: float | None = Field(None, description="Area in dunams (farm mode)")
    crop_name: str | None = Field(None, description="Crop name (farm mode)")
    stage: str | None = Field(None, description="Crop stage: 'initial', 'mid', 'late' (farm mode)")

    # Plant mode fields
    pot_volume_liters: float | None = Field(None, description="Pot volume in liters (plant mode)")
    pot_diameter_cm: float | None = Field(None, description="Pot diameter in cm (plant mode)")
    plant_profile_name: str | None = Field(None, description="Plant profile name (plant mode)")
    indoor_outdoor: Literal["indoor", "outdoor"] | None = Field(
        "indoor", description="Indoor or outdoor (plant mode)"
    )

    # Common fields
    irrigation_method: str | None = Field(
        None, description="Irrigation method (e.g., 'drip', 'sprinkler')"
    )
    efficiency: float | None = Field(
        None, ge=0.0, le=1.0, description="Irrigation system efficiency (0-1)"
    )

    @model_validator(mode="after")
    def validate_mode_fields(self):
        """Validate that required fields are present based on mode."""
        if self.mode == "farm":
            if not self.area_m2 and not self.area_dunam:
                raise ValueError("Farm mode requires either area_m2 or area_dunam")
            if not self.crop_name:
                raise ValueError("Farm mode requires crop_name")
        elif self.mode == "plant":
            if not self.pot_volume_liters and not self.pot_diameter_cm:
                raise ValueError("Plant mode requires either pot_volume_liters or pot_diameter_cm")
            if not self.plant_profile_name:
                raise ValueError("Plant mode requires plant_profile_name")
        return self


class ForecastPoint(BaseModel):
    """Normalized forecast data point."""

    date: datetime.date = Field(..., description="Forecast date")
    lat: float = Field(..., description="Point latitude")
    lon: float = Field(..., description="Point longitude")
    evap_mm: float = Field(
        ...,
        description=(
            "Daily evaporation in mm. "
            "For MoAG forecast: represents daily evaporation (exact method TBD - "
            "may be ET0 Penman-Monteith, open-pan evaporation, or other). "
            "Used as ET0 proxy in irrigation calculations. "
            "See ai_docs/specs/coefficients_sources.md for details."
        ),
    )
    temp_min: float | None = Field(None, description="Minimum temperature (°C)")
    temp_max: float | None = Field(None, description="Maximum temperature (°C)")
    name: str | None = Field(None, description="Station/point name")
    geographic_area: str | None = Field(None, description="Geographic area identifier")


class IrrigationPlan(BaseModel):
    """Computed irrigation plan output."""

    date: datetime.date = Field(..., description="Plan date")
    mode: Literal["farm", "plant"] = Field(..., description="Mode: 'farm' or 'plant'")

    # Farm mode outputs
    liters_per_day: float | None = Field(None, description="Liters per day (farm mode)")
    liters_per_dunam: float | None = Field(None, description="Liters per dunam (farm mode)")

    # Plant mode outputs
    ml_per_day: float | None = Field(None, description="Milliliters per day (plant mode)")

    # Common outputs
    pulses_per_day: int = Field(..., description="Number of irrigation pulses per day")
    inputs_used: dict[str, float | str] = Field(
        ..., description="Inputs used in computation (kc, efficiency, area_m2, evap_mm)"
    )
    coefficient_value_used: float = Field(
        ..., description="Kc coefficient value used in calculation"
    )
    coefficient_source: dict[str, str | None] = Field(
        ...,
        description=(
            "Source information: source_type (israeli_calendar_monthly, "
            "israeli_calendar_decadal, fao56_stage), source_title, source_url, "
            "table_reference (optional)"
        ),
    )
    warnings: list[str] = Field(default_factory=list, description="Warnings (e.g., unknown crop)")

    # Optional human-readable outputs
    schedule: str | None = Field(None, description="Recommended schedule/pulse timing")
    card_text: str | None = Field(None, description="Shareable card text (plant mode)")
