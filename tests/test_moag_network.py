"""
Network tests for MoAG API client.

These tests require network access and are skipped by default.
Run with: pytest -m network
"""

import pytest

from app.data import get_forecast_points
from app.data.moag_client import MoAGClientError


@pytest.mark.network
def test_fetch_forecast_real_api():
    """Test fetching forecast from real MoAG API (requires network)."""
    from datetime import datetime

    today = datetime.now().date().isoformat()
    try:
        points = get_forecast_points(date_str=today, offline_mode=False)
        assert len(points) > 0, "Should return at least one forecast point"
        # Verify structure
        point = points[0]
        assert hasattr(point, "date")
        assert hasattr(point, "lat")
        assert hasattr(point, "lon")
        assert hasattr(point, "evap_mm")
        assert point.evap_mm > 0, "Evap should be positive"
    except MoAGClientError as e:
        pytest.skip(f"MoAG API unavailable (this is expected): {e}")

