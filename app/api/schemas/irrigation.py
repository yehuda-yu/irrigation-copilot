"""
Irrigation API schemas.
"""

import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.domain.models import IrrigationPlan


class IrrigationPlanRequest(BaseModel):
    """Request schema for deterministic irrigation planning."""

    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    date: Optional[str] = Field(None, description="Forecast date (YYYY-MM-DD), defaults to today")
    offline: Optional[bool] = Field(None, description="If True, only use cached data")
    mode: Literal["farm", "plant"] = Field(..., description="Mode: 'farm' or 'plant'")

    # Farm mode fields
    crop_name: Optional[str] = Field(None, description="Crop name (farm mode)")
    stage: Optional[Literal["initial", "mid", "late"]] = Field(
        None, description="Crop stage (farm mode)"
    )
    area_dunam: Optional[float] = Field(None, description="Area in dunams (farm mode)")
    irrigation_method: Optional[str] = Field(None, description="Irrigation method (farm mode)")
    efficiency: Optional[float] = Field(None, ge=0.0, le=1.0, description="System efficiency (0-1)")

    # Plant mode fields
    plant_profile: Optional[str] = Field(None, description="Plant profile name (plant mode)")
    pot_diameter_cm: Optional[float] = Field(None, description="Pot diameter in cm (plant mode)")
    pot_volume_l: Optional[float] = Field(None, description="Pot volume in liters (plant mode)")

    @model_validator(mode="after")
    def validate_mode_fields(self):
        """Validate required fields based on mode."""
        if self.mode == "farm":
            if not self.crop_name:
                raise ValueError("Farm mode requires crop_name")
            if not self.area_dunam:
                raise ValueError("Farm mode requires area_dunam")
        elif self.mode == "plant":
            if not self.plant_profile:
                raise ValueError("Plant mode requires plant_profile")
            if not self.pot_diameter_cm and not self.pot_volume_l:
                raise ValueError("Plant mode requires either pot_diameter_cm or pot_volume_l")
        return self


class ChosenPointInfo(BaseModel):
    """Diagnostics for selected forecast point."""

    name: Optional[str] = None
    area: Optional[str] = None
    lat: float
    lon: float
    distance_km: float
    date: datetime.date


class IrrigationPlanResponse(BaseModel):
    """Response schema for irrigation planning."""

    plan: IrrigationPlan
    chosen_point: ChosenPointInfo
    date_used: str
    evap_mm_used: float
    warnings: list[str] = []

