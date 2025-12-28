"""
Irrigation planning routes.
"""

import logging
from datetime import datetime

from fastapi import APIRouter

from app.api.errors import map_domain_error_to_http
from app.api.schemas.irrigation import (
    ChosenPointInfo,
    IrrigationPlanRequest,
    IrrigationPlanResponse,
)
from app.data.forecast_service import get_forecast_points
from app.data.station_matching import haversine_km, pick_nearest_point
from app.domain.irrigation_engine import compute_plan
from app.domain.models import ProfileInput

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/plan", response_model=IrrigationPlanResponse)
async def create_irrigation_plan(request: IrrigationPlanRequest):
    """
    Generate a deterministic irrigation plan based on location and plant/crop info.
    """
    try:
        # 1. Resolve date
        date_used = request.date or datetime.now().date().isoformat()

        # 2. Get forecast points
        points = get_forecast_points(date_str=date_used, offline_mode=request.offline)

        # 3. Pick nearest point
        chosen_point = pick_nearest_point(request.lat, request.lon, points)
        distance_km = haversine_km(request.lat, request.lon, chosen_point.lat, chosen_point.lon)

        # 4. Map request to ProfileInput (Domain Model)
        # Note: request fields might need mapping to ProfileInput fields
        profile = ProfileInput(
            mode=request.mode,
            lat=request.lat,
            lon=request.lon,
            area_dunam=request.area_dunam,
            crop_name=request.crop_name,
            stage=request.stage,
            plant_profile_name=request.plant_profile,
            pot_diameter_cm=request.pot_diameter_cm,
            pot_volume_liters=request.pot_volume_l,
            irrigation_method=request.irrigation_method,
            efficiency=request.efficiency,
        )

        # 5. Compute plan
        plan = compute_plan(profile, chosen_point)

        # 6. Build response
        response = IrrigationPlanResponse(
            plan=plan,
            chosen_point=ChosenPointInfo(
                name=chosen_point.name,
                area=chosen_point.geographic_area,
                lat=chosen_point.lat,
                lon=chosen_point.lon,
                distance_km=distance_km,
                date=chosen_point.date,
            ),
            date_used=date_used,
            evap_mm_used=chosen_point.evap_mm,
            warnings=plan.warnings,
        )
        return response

    except Exception as e:
        logger.error(f"Error in /irrigation/plan: {str(e)}")
        raise map_domain_error_to_http(e)
