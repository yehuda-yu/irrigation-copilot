"""
Station matching logic.

Matches user location (lat/lon) to nearest forecast point or weather station.
Used by pick_point tool to select appropriate forecast data.
"""

import math
from dataclasses import dataclass

from app.domain.models import ForecastPoint

# Tolerance for "near-tie" distance comparisons (1 meter in kilometers)
# Points within this distance are considered tied and use deterministic tie-breaker
EPSILON_KM = 0.001  # 1 meter


class InvalidCoordinatesError(ValueError):
    """
    Raised when all forecast points have invalid coordinates.

    Attributes:
        total_points: Total number of points provided
        skipped_count: Number of points skipped due to invalid coordinates
        skipped_points: List of (name, area, lat, lon) tuples for skipped points
    """

    def __init__(
        self,
        message: str,
        total_points: int,
        skipped_count: int,
        skipped_points: list[tuple[str | None, str | None, float, float]],
    ):
        super().__init__(message)
        self.total_points = total_points
        self.skipped_count = skipped_count
        self.skipped_points = skipped_points


@dataclass
class SelectionDiagnostics:
    """Diagnostics for point selection process."""

    total_points: int
    valid_points: int
    skipped_count: int
    skipped_points: list[tuple[str | None, str | None, float, float]]


def _validate_user_coordinates(lat: float, lon: float) -> None:
    """
    Validate user-provided coordinates (strict validation).

    Raises ValueError for out-of-range values.

    Args:
        lat: User latitude
        lon: User longitude

    Raises:
        ValueError: If coordinates are outside valid ranges
    """
    if not (-90 <= lat <= 90):
        raise ValueError(f"User latitude must be between -90 and 90. Got: {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"User longitude must be between -180 and 180. Got: {lon}")


def _is_valid_coordinate(lat: float, lon: float) -> bool:
    """
    Check if coordinates are valid (for source ForecastPoint validation).

    Returns False for out-of-range values (graceful handling).

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        True if coordinates are valid, False otherwise
    """
    return (-90 <= lat <= 90) and (-180 <= lon <= 180)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.

    Args:
        lat1, lon1: First point coordinates (latitude, longitude)
        lat2, lon2: Second point coordinates (latitude, longitude)

    Returns:
        Distance in kilometers

    Raises:
        ValueError: If coordinates are outside valid ranges
    """
    # Validate latitude range [-90, 90]
    if not (-90 <= lat1 <= 90) or not (-90 <= lat2 <= 90):
        raise ValueError(
            f"Latitude must be between -90 and 90. Got: lat1={lat1}, lat2={lat2}"
        )

    # Validate longitude range [-180, 180]
    if not (-180 <= lon1 <= 180) or not (-180 <= lon2 <= 180):
        raise ValueError(
            f"Longitude must be between -180 and 180. Got: lon1={lon1}, lon2={lon2}"
        )

    # Earth radius in kilometers
    earth_radius_km = 6371.0

    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    distance_km = earth_radius_km * c
    return distance_km


def pick_nearest_point(
    user_lat: float, user_lon: float, points: list[ForecastPoint]
) -> ForecastPoint:
    """
    Select the nearest forecast point to user location.

    Uses epsilon tolerance for "near-tie" handling: points within EPSILON_KM
    (1 meter) are considered tied and use deterministic tie-breaker.

    Args:
        user_lat: User latitude (strictly validated)
        user_lon: User longitude (strictly validated)
        points: List of ForecastPoint objects

    Returns:
        Nearest ForecastPoint

    Raises:
        ValueError: If user coordinates are invalid or points list is empty
        InvalidCoordinatesError: If all points have invalid coordinates
            (includes diagnostics: total_points, skipped_count, skipped_points)
    """
    # Strict validation for user input
    _validate_user_coordinates(user_lat, user_lon)

    if not points:
        raise ValueError("Cannot select nearest point: points list is empty")

    # Calculate distances to all points, tracking skipped ones
    distances = []
    skipped_points = []
    for point in points:
        # Graceful handling for source data: check validity before computing distance
        if not _is_valid_coordinate(point.lat, point.lon):
            skipped_points.append((point.name, point.geographic_area, point.lat, point.lon))
            continue

        try:
            distance_km = haversine_km(user_lat, user_lon, point.lat, point.lon)
            distances.append((point, distance_km))
        except ValueError:
            # Should not happen if _is_valid_coordinate check passed,
            # but handle gracefully just in case
            skipped_points.append((point.name, point.geographic_area, point.lat, point.lon))
            continue

    if not distances:
        # Raise specific exception with diagnostics
        error_msg = (
            f"Cannot select nearest point: all {len(points)} point(s) have invalid coordinates. "
            f"Skipped {len(skipped_points)} point(s)."
        )
        raise InvalidCoordinatesError(
            error_msg,
            total_points=len(points),
            skipped_count=len(skipped_points),
            skipped_points=skipped_points,
        )

    # Find minimum distance
    min_distance = min(dist for _, dist in distances)

    # Collect all points at minimum distance OR within epsilon (near-tie handling)
    # Use epsilon tolerance instead of exact equality
    candidates = [
        point
        for point, dist in distances
        if abs(dist - min_distance) <= EPSILON_KM
    ]

    if len(candidates) == 1:
        return candidates[0]

    # Tie-breaker: sort deterministically by (geographic_area, name, lat, lon)
    # Use tuple comparison for deterministic ordering
    candidates.sort(
        key=lambda p: (
            p.geographic_area or "",
            p.name or "",
            p.lat,
            p.lon,
        )
    )

    return candidates[0]


def get_nearest_points(
    user_lat: float,
    user_lon: float,
    points: list[ForecastPoint],
    k: int = 3,
) -> list[tuple[ForecastPoint, float]]:
    """
    Get k nearest forecast points to user location with distances.

    Useful for debugging and agent UI ("I picked X, alternatives Y/Z").

    Args:
        user_lat: User latitude (strictly validated)
        user_lon: User longitude (strictly validated)
        points: List of ForecastPoint objects
        k: Number of nearest points to return (default: 3)

    Returns:
        List of tuples (ForecastPoint, distance_km), sorted by distance (nearest first)

    Raises:
        ValueError: If user coordinates are invalid or points list is empty
        InvalidCoordinatesError: If all points have invalid coordinates
            (includes diagnostics: total_points, skipped_count, skipped_points)
    """
    # Strict validation for user input
    _validate_user_coordinates(user_lat, user_lon)

    if not points:
        raise ValueError("Cannot get nearest points: points list is empty")

    # Calculate distances to all points, tracking skipped ones
    distances = []
    skipped_points = []
    for point in points:
        # Graceful handling for source data: check validity before computing distance
        if not _is_valid_coordinate(point.lat, point.lon):
            skipped_points.append((point.name, point.geographic_area, point.lat, point.lon))
            continue

        try:
            distance_km = haversine_km(user_lat, user_lon, point.lat, point.lon)
            distances.append((point, distance_km))
        except ValueError:
            # Should not happen if _is_valid_coordinate check passed,
            # but handle gracefully just in case
            skipped_points.append((point.name, point.geographic_area, point.lat, point.lon))
            continue

    if not distances:
        # Raise specific exception with diagnostics
        error_msg = (
            f"Cannot get nearest points: all {len(points)} point(s) have invalid coordinates. "
            f"Skipped {len(skipped_points)} point(s)."
        )
        raise InvalidCoordinatesError(
            error_msg,
            total_points=len(points),
            skipped_count=len(skipped_points),
            skipped_points=skipped_points,
        )

    # Sort by distance (nearest first)
    distances.sort(key=lambda x: x[1])

    # Return top k
    return distances[:k]


def get_selection_diagnostics(
    user_lat: float, user_lon: float, points: list[ForecastPoint]
) -> SelectionDiagnostics:
    """
    Get diagnostics about point selection process.

    Useful for debugging and understanding data quality.

    Args:
        user_lat: User latitude (strictly validated)
        user_lon: User longitude (strictly validated)
        points: List of ForecastPoint objects

    Returns:
        SelectionDiagnostics with counts and skipped point details

    Raises:
        ValueError: If user coordinates are invalid
    """
    # Strict validation for user input
    _validate_user_coordinates(user_lat, user_lon)

    skipped_points = []
    valid_count = 0

    for point in points:
        if not _is_valid_coordinate(point.lat, point.lon):
            skipped_points.append((point.name, point.geographic_area, point.lat, point.lon))
        else:
            valid_count += 1

    return SelectionDiagnostics(
        total_points=len(points),
        valid_points=valid_count,
        skipped_count=len(skipped_points),
        skipped_points=skipped_points,
    )


# Legacy alias for backwards compatibility
def find_nearest_point(
    forecast_points: list[ForecastPoint],
    lat: float,
    lon: float,
) -> ForecastPoint:
    """
    Find nearest forecast point to user location.

    Legacy alias for pick_nearest_point().

    Args:
        forecast_points: Available forecast points
        lat: User latitude
        lon: User longitude

    Returns:
        Nearest ForecastPoint

    Raises:
        ValueError: If no forecast points provided
    """
    return pick_nearest_point(lat, lon, forecast_points)


# Legacy alias for backwards compatibility
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates (Haversine formula).

    Legacy alias for haversine_km().

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in kilometers
    """
    return haversine_km(lat1, lon1, lat2, lon2)
