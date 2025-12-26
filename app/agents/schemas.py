"""
Agent result schemas (Pydantic models).

Structured outputs from the agent for irrigation planning.
"""

import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.models import IrrigationPlan, ProfileInput


class ChosenPointInfo(BaseModel):
    """Information about the selected forecast point."""

    name: str | None = Field(None, description="Point/station name")
    geographic_area: str | None = Field(None, description="Geographic area")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    distance_km: float = Field(..., description="Distance from user location in km")
    date: datetime.date = Field(..., description="Forecast date")
    evap_mm: float = Field(..., description="Evaporation in mm")


class IrrigationAgentResult(BaseModel):
    """Structured result from irrigation agent."""

    answer_text: str = Field(
        ...,
        description="Short human-readable answer (2-6 lines) explaining the recommendation",
    )
    plan: IrrigationPlan = Field(..., description="Computed irrigation plan")
    chosen_point: ChosenPointInfo = Field(..., description="Selected forecast point information")
    inputs_used: ProfileInput = Field(..., description="User inputs used in computation")
    warnings: list[str] = Field(default_factory=list, description="Warnings and cautions")
    debug: dict[str, Any] | None = Field(
        None, description="Optional debug information (tool timings, etc.)"
    )

