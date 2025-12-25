"""
Tests for geospatial nearest-point selection.

All tests are offline and deterministic.
"""

import datetime

import pytest

from app.data.station_matching import (
    EPSILON_KM,
    InvalidCoordinatesError,
    get_nearest_points,
    get_selection_diagnostics,
    haversine_km,
    pick_nearest_point,
)
from app.domain.models import ForecastPoint


def test_haversine_zero_distance():
    """Test that distance to self is zero."""
    lat, lon = 32.0853, 34.7818
    distance = haversine_km(lat, lon, lat, lon)
    assert distance == 0.0


def test_haversine_known_distance():
    """Test Haversine with known distance (Tel Aviv to Jerusalem ~54km)."""
    # Tel Aviv coordinates
    ta_lat, ta_lon = 32.0853, 34.7818
    # Jerusalem coordinates
    jlm_lat, jlm_lon = 31.7683, 35.2137

    distance = haversine_km(ta_lat, ta_lon, jlm_lat, jlm_lon)
    # Should be approximately 54km (allow 5km tolerance)
    assert 50 <= distance <= 60


def test_haversine_invalid_latitude():
    """Test that invalid latitude raises ValueError."""
    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        haversine_km(91, 0, 0, 0)

    with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
        haversine_km(0, 0, -91, 0)


def test_haversine_invalid_longitude():
    """Test that invalid longitude raises ValueError."""
    with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
        haversine_km(0, 181, 0, 0)

    with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
        haversine_km(0, 0, 0, -181)


def test_pick_nearest_point_basic():
    """Test basic nearest point selection."""
    # User location: Tel Aviv
    user_lat, user_lon = 32.0853, 34.7818

    # Create test points
    points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.0,
            lon=34.7,
            evap_mm=5.0,
            name="Point A",
            geographic_area="South",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.1,
            lon=34.8,
            evap_mm=5.5,
            name="Point B",
            geographic_area="Center",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            lat=31.7,
            lon=35.2,
            evap_mm=4.5,
            name="Point C",
            geographic_area="Jerusalem",
        ),
    ]

    nearest = pick_nearest_point(user_lat, user_lon, points)
    # Point B should be nearest (closest to Tel Aviv)
    assert nearest.name == "Point B"
    assert nearest.lat == 32.1
    assert nearest.lon == 34.8


def test_pick_nearest_point_empty_list_raises():
    """Test that empty points list raises ValueError."""
    with pytest.raises(ValueError, match="Cannot select nearest point: points list is empty"):
        pick_nearest_point(32.0, 34.0, [])


def test_pick_nearest_point_invalid_coords_raises():
    """Test that points with invalid coordinates are skipped, but error if all invalid."""
    user_lat, user_lon = 32.0, 34.0

    # All points have invalid coordinates
    points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=91.0,  # Invalid
            lon=34.0,
            evap_mm=5.0,
            name="Invalid Point 1",
            geographic_area="Area A",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.0,
            lon=181.0,  # Invalid
            evap_mm=5.0,
            name="Invalid Point 2",
            geographic_area="Area B",
        ),
    ]

    with pytest.raises(InvalidCoordinatesError) as exc_info:
        pick_nearest_point(user_lat, user_lon, points)

    # Verify diagnostics
    assert exc_info.value.total_points == 2
    assert exc_info.value.skipped_count == 2
    assert len(exc_info.value.skipped_points) == 2
    # Check that skipped points include the names
    skipped_names = [name for name, _, _, _ in exc_info.value.skipped_points]
    assert "Invalid Point 1" in skipped_names
    assert "Invalid Point 2" in skipped_names


def test_pick_nearest_point_skips_invalid_coords():
    """Test that points with invalid coordinates are skipped, valid ones used."""
    user_lat, user_lon = 32.0, 34.0

    points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=91.0,  # Invalid - should be skipped
            lon=34.0,
            evap_mm=5.0,
            name="Invalid Point",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.1,  # Valid - should be selected
            lon=34.1,
            evap_mm=5.0,
            name="Valid Point",
        ),
    ]

    nearest = pick_nearest_point(user_lat, user_lon, points)
    assert nearest.name == "Valid Point"


def test_tie_breaker_is_deterministic():
    """Test that tie-breaker is deterministic when distances are equal."""
    # User location
    user_lat, user_lon = 32.0, 34.0

    # Create points at exactly the same location (distance = 0 for both)
    # This guarantees equal distance, so tie-breaker will be used
    points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=user_lat,
            lon=user_lon,  # Same location as user (distance = 0)
            evap_mm=5.0,
            name="Point Z",
            geographic_area="Area B",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            lat=user_lat,
            lon=user_lon,  # Same location as user (distance = 0)
            evap_mm=5.0,
            name="Point A",
            geographic_area="Area A",
        ),
    ]

    # Should pick deterministically by (geographic_area, name, lat, lon)
    nearest = pick_nearest_point(user_lat, user_lon, points)
    # Area A comes before Area B alphabetically
    assert nearest.geographic_area == "Area A"
    assert nearest.name == "Point A"

    # Verify it's deterministic (run multiple times)
    for _ in range(10):
        result = pick_nearest_point(user_lat, user_lon, points)
        assert result.name == "Point A"


def test_get_nearest_points_basic():
    """Test get_nearest_points returns k nearest with distances."""
    user_lat, user_lon = 32.0, 34.0

    points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.0,
            lon=34.0,  # Closest (same location)
            evap_mm=5.0,
            name="Point A",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.1,
            lon=34.1,  # Second closest
            evap_mm=5.0,
            name="Point B",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            lat=31.7,
            lon=35.2,  # Farthest
            evap_mm=5.0,
            name="Point C",
        ),
    ]

    top3 = get_nearest_points(user_lat, user_lon, points, k=3)
    assert len(top3) == 3

    # Check distances are sorted (nearest first)
    distances = [dist for _, dist in top3]
    assert distances == sorted(distances)

    # First should be Point A (distance ~0)
    assert top3[0][0].name == "Point A"
    assert top3[0][1] < 1.0  # Very close to 0

    # Second should be Point B
    assert top3[1][0].name == "Point B"


def test_get_nearest_points_k_larger_than_available():
    """Test that k larger than available points returns all points."""
    user_lat, user_lon = 32.0, 34.0

    points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.1,
            lon=34.1,
            evap_mm=5.0,
            name="Point A",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.2,
            lon=34.2,
            evap_mm=5.0,
            name="Point B",
        ),
    ]

    top5 = get_nearest_points(user_lat, user_lon, points, k=5)
    assert len(top5) == 2  # Only 2 points available


def test_get_nearest_points_empty_list_raises():
    """Test that empty points list raises ValueError."""
    with pytest.raises(ValueError, match="Cannot get nearest points: points list is empty"):
        get_nearest_points(32.0, 34.0, [], k=3)


def test_pick_nearest_point_near_tie_uses_epsilon():
    """Test that near-tie handling uses epsilon tolerance for floating-point comparisons."""
    user_lat, user_lon = 32.0, 34.0

    # Create points that are very close in distance (within epsilon = 0.001 km = 1 meter)
    # Use actual distance calculation to ensure they're within epsilon
    # Point A: at distance d
    # Point B: at distance d + epsilon/2 (within epsilon, should be tied)
    base_lat = 32.001  # ~111 meters north
    base_lon = 34.0

    points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=base_lat,
            lon=base_lon,
            evap_mm=5.0,
            name="Point A",
            geographic_area="Area A",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            # Place Point B such that its distance is within epsilon of Point A's distance
            # Move slightly north (EPSILON_KM/2 in degrees ≈ 0.0000045 degrees)
            lat=base_lat + (EPSILON_KM / 2) / 111.0,
            lon=base_lon,
            evap_mm=5.0,
            name="Point B",
            geographic_area="Area B",
        ),
    ]

    # Calculate actual distances
    dist_a = haversine_km(user_lat, user_lon, points[0].lat, points[0].lon)
    dist_b = haversine_km(user_lat, user_lon, points[1].lat, points[1].lon)

    # Verify they're within epsilon
    assert abs(dist_b - dist_a) <= EPSILON_KM

    # Both points should be considered tied (within epsilon)
    # Tie-breaker should select Area A (alphabetically first)
    nearest = pick_nearest_point(user_lat, user_lon, points)
    assert nearest.geographic_area == "Area A"
    assert nearest.name == "Point A"


def test_pick_nearest_point_near_tie_epsilon_boundary():
    """Test that points just outside epsilon are NOT considered tied."""
    user_lat, user_lon = 32.0, 34.0

    # Create points where one is just outside epsilon
    # Point A: closer (should be selected)
    # Point B: just outside epsilon (should NOT be tied)
    base_lat = 32.001  # ~111 meters north
    base_lon = 34.0

    points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=base_lat,
            lon=base_lon,
            evap_mm=5.0,
            name="Point A",
            geographic_area="Area A",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            # Place Point B such that its distance is just outside epsilon
            # Move north by EPSILON_KM * 1.1 in degrees
            lat=base_lat + (EPSILON_KM * 1.1) / 111.0,
            lon=base_lon,
            evap_mm=5.0,
            name="Point B",
            geographic_area="Area B",
        ),
    ]

    # Calculate actual distances
    dist_a = haversine_km(user_lat, user_lon, points[0].lat, points[0].lon)
    dist_b = haversine_km(user_lat, user_lon, points[1].lat, points[1].lon)

    # Verify they're outside epsilon
    assert abs(dist_b - dist_a) > EPSILON_KM

    # Point A should be selected (not tied, since B is outside epsilon)
    nearest = pick_nearest_point(user_lat, user_lon, points)
    assert nearest.name == "Point A"


def test_get_nearest_points_invalid_coords_raises():
    """Test that get_nearest_points raises InvalidCoordinatesError with diagnostics."""
    user_lat, user_lon = 32.0, 34.0

    points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=91.0,  # Invalid
            lon=34.0,
            evap_mm=5.0,
            name="Invalid Point",
        ),
    ]

    with pytest.raises(InvalidCoordinatesError) as exc_info:
        get_nearest_points(user_lat, user_lon, points, k=3)

    assert exc_info.value.total_points == 1
    assert exc_info.value.skipped_count == 1


def test_pick_nearest_point_user_invalid_coords_raises():
    """Test that invalid user coordinates raise ValueError (strict validation)."""
    valid_points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.0,
            lon=34.0,
            evap_mm=5.0,
        ),
    ]

    # Invalid user latitude
    with pytest.raises(ValueError, match="User latitude must be between -90 and 90"):
        pick_nearest_point(91.0, 34.0, valid_points)

    # Invalid user longitude
    with pytest.raises(ValueError, match="User longitude must be between -180 and 180"):
        pick_nearest_point(32.0, 181.0, valid_points)


def test_get_selection_diagnostics():
    """Test that get_selection_diagnostics returns correct counts and skipped points."""
    user_lat, user_lon = 32.0, 34.0

    points = [
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.0,
            lon=34.0,
            evap_mm=5.0,
            name="Valid Point 1",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            lat=91.0,  # Invalid
            lon=34.0,
            evap_mm=5.0,
            name="Invalid Point",
            geographic_area="Area X",
        ),
        ForecastPoint(
            date=datetime.date.today(),
            lat=32.1,
            lon=34.1,
            evap_mm=5.0,
            name="Valid Point 2",
        ),
    ]

    diagnostics = get_selection_diagnostics(user_lat, user_lon, points)

    assert diagnostics.total_points == 3
    assert diagnostics.valid_points == 2
    assert diagnostics.skipped_count == 1
    assert len(diagnostics.skipped_points) == 1
    assert diagnostics.skipped_points[0][0] == "Invalid Point"
    assert diagnostics.skipped_points[0][1] == "Area X"

