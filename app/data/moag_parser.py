"""
MoAG forecast data parser.

Parses raw MoAG API responses into normalized ForecastPoint models.
Handles data validation and normalization.
"""

import datetime
import logging
from typing import Any

from app.domain.models import ForecastPoint

logger = logging.getLogger(__name__)


def parse_forecast_points(payload: dict[str, Any]) -> list[ForecastPoint]:
    """
    Parse raw MoAG API response into ForecastPoint list.

    Extracts all records across areas/locations/dates and normalizes them.

    Args:
        payload: Raw API response dictionary

    Returns:
        List of normalized ForecastPoint objects

    Raises:
        ValueError: If payload structure is invalid
    """
    total_locations_seen = 0
    total_records_emitted = 0
    skipped_records = 0

    forecast_points: list[ForecastPoint] = []

    try:
        # Navigate to tempEvapRecord -> areas
        temp_evap_record = payload.get("tempEvapRecord", {})
        if not temp_evap_record:
            logger.warning("Payload missing 'tempEvapRecord' key")
            return []

        areas = temp_evap_record.get("areas", {})
        if not isinstance(areas, dict):
            logger.warning("Payload 'areas' is not a dictionary")
            return []

        # Iterate through areas
        for area_name, locations in areas.items():
            if not isinstance(locations, list):
                logger.debug(f"Skipping area '{area_name}': locations is not a list")
                continue

            # Iterate through locations in this area
            for location in locations:
                total_locations_seen += 1

                if not isinstance(location, dict):
                    logger.debug(f"Skipping location in area '{area_name}': not a dict")
                    skipped_records += 1
                    continue

                # Extract location metadata
                name = location.get("name")
                lat_raw = location.get("lat") or location.get("latitude")
                lon_raw = location.get("long") or location.get("longitude") or location.get("lon")
                data = location.get("data", {})

                if not isinstance(data, dict):
                    logger.debug(f"Skipping location '{name}': data is not a dict")
                    skipped_records += 1
                    continue

                # Parse coordinates
                try:
                    lat = float(lat_raw) if lat_raw is not None else None
                    lon = float(lon_raw) if lon_raw is not None else None
                except (ValueError, TypeError):
                    logger.debug(
                        f"Skipping location '{name}': invalid coordinates "
                        f"(lat={lat_raw}, lon={lon_raw})"
                    )
                    skipped_records += 1
                    continue

                if lat is None or lon is None:
                    logger.debug(f"Skipping location '{name}': missing coordinates")
                    skipped_records += 1
                    continue

                # Iterate through dates in this location's data
                for date_str, date_data in data.items():
                    if not isinstance(date_data, dict):
                        logger.debug(
                            f"Skipping date '{date_str}' for location '{name}': data is not a dict"
                        )
                        skipped_records += 1
                        continue

                    # Parse date
                    try:
                        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        logger.debug(
                            f"Skipping date '{date_str}' for location '{name}': invalid date format"
                        )
                        skipped_records += 1
                        continue

                    # Extract evap, temp_min, temp_max
                    # Note: MoAG "evap" field semantics are not fully documented.
                    # It is used as an ET0 proxy in calculations, but the exact method
                    # (Penman-Monteith, open-pan, etc.) should be verified with MoAG.
                    evap_raw = date_data.get("evap")
                    temp_min_raw = date_data.get("temp_min")
                    temp_max_raw = date_data.get("temp_max")

                    # Evap is required
                    try:
                        evap_mm = float(evap_raw) if evap_raw is not None else None
                    except (ValueError, TypeError):
                        logger.debug(
                            f"Skipping record: location '{name}', date '{date_str}': "
                            f"invalid evap value '{evap_raw}'"
                        )
                        skipped_records += 1
                        continue

                    if evap_mm is None:
                        logger.debug(
                            f"Skipping record: location '{name}', date '{date_str}': missing evap"
                        )
                        skipped_records += 1
                        continue

                    # Temps are optional
                    temp_min = None
                    temp_max = None
                    try:
                        if temp_min_raw is not None:
                            temp_min = float(temp_min_raw)
                        if temp_max_raw is not None:
                            temp_max = float(temp_max_raw)
                    except (ValueError, TypeError):
                        # Log but don't skip - temps are optional
                        logger.debug(
                            f"Invalid temp values for location '{name}', date '{date_str}': "
                            f"temp_min={temp_min_raw}, temp_max={temp_max_raw}"
                        )

                    # Create ForecastPoint
                    try:
                        point = ForecastPoint(
                            date=date_obj,
                            lat=lat,
                            lon=lon,
                            evap_mm=evap_mm,
                            temp_min=temp_min,
                            temp_max=temp_max,
                            name=str(name) if name is not None else None,
                            geographic_area=str(area_name) if area_name else None,
                        )
                        forecast_points.append(point)
                        total_records_emitted += 1
                    except Exception as e:
                        logger.debug(
                            f"Skipping record: location '{name}', date '{date_str}': "
                            f"ForecastPoint validation failed: {e}"
                        )
                        skipped_records += 1
                        continue

    except Exception as e:
        logger.error(f"Unexpected error parsing forecast payload: {e}")
        raise ValueError(f"Failed to parse forecast payload: {e}") from e

    # Log summary
    logger.info(
        f"Parsed forecast: {total_locations_seen} locations seen, "
        f"{total_records_emitted} records emitted, {skipped_records} skipped"
    )

    return forecast_points
