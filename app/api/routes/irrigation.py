"""
Irrigation plan API routes.

Endpoints for generating irrigation recommendations:
- POST /irrigation/plan - Generate irrigation plan from user profile
- GET /irrigation/forecast - Get forecast summary for location
"""

from fastapi import APIRouter

router = APIRouter(prefix="/irrigation", tags=["irrigation"])


@router.post("/plan")
async def create_irrigation_plan():
    """Generate irrigation plan from user profile."""
    # TODO: Implement
    pass


@router.get("/forecast")
async def get_forecast():
    """Get forecast summary for location."""
    # TODO: Implement
    pass
