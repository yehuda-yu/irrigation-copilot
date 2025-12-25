"""
MoAG parser tests.

Offline, deterministic tests for forecast parsing logic.
"""

import datetime

from app.data.moag_parser import parse_forecast_points


def test_parse_forecast_points_happy_path():
    """Test parser with valid payload structure."""
    payload = {
        "tempEvapRecord": {
            "areas": {
                "North": [
                    {
                        "name": "Station A",
                        "lat": 32.5,
                        "long": 34.8,
                        "data": {
                            "2024-01-15": {
                                "evap": 5.2,
                                "temp_min": 10.0,
                                "temp_max": 20.0,
                            },
                            "2024-01-16": {
                                "evap": 5.5,
                                "temp_min": 11.0,
                                "temp_max": 21.0,
                            },
                        },
                    },
                    {
                        "name": "Station B",
                        "lat": 33.0,
                        "lon": 35.0,
                        "data": {
                            "2024-01-15": {
                                "evap": 4.8,
                                "temp_min": 9.0,
                                "temp_max": 19.0,
                            },
                        },
                    },
                ],
                "South": [
                    {
                        "name": "Station C",
                        "latitude": 31.0,
                        "longitude": 34.5,
                        "data": {
                            "2024-01-15": {
                                "evap": 6.0,
                                "temp_min": 12.0,
                                "temp_max": 22.0,
                            },
                        },
                    },
                ],
            }
        }
    }

    points = parse_forecast_points(payload)

    assert len(points) == 4, f"Expected 4 points, got {len(points)}"

    # Check first point (Station A, 2024-01-15)
    point1 = next(
        p for p in points if p.name == "Station A" and p.date == datetime.date(2024, 1, 15)
    )
    assert point1.lat == 32.5
    assert point1.lon == 34.8
    assert point1.evap_mm == 5.2
    assert point1.temp_min == 10.0
    assert point1.temp_max == 20.0
    assert point1.geographic_area == "North"

    # Check second point (Station A, 2024-01-16)
    point2 = next(
        p for p in points if p.name == "Station A" and p.date == datetime.date(2024, 1, 16)
    )
    assert point2.evap_mm == 5.5
    assert point2.temp_min == 11.0
    assert point2.temp_max == 21.0

    # Check Station B (uses "lon" instead of "long")
    point3 = next(p for p in points if p.name == "Station B")
    assert point3.lat == 33.0
    assert point3.lon == 35.0
    assert point3.evap_mm == 4.8

    # Check Station C (uses "latitude"/"longitude")
    point4 = next(p for p in points if p.name == "Station C")
    assert point4.lat == 31.0
    assert point4.lon == 34.5
    assert point4.geographic_area == "South"


def test_parse_skips_bad_records():
    """Test parser skips malformed records and continues processing."""
    payload = {
        "tempEvapRecord": {
            "areas": {
                "North": [
                    # Valid record
                    {
                        "name": "Good Station",
                        "lat": 32.5,
                        "long": 34.8,
                        "data": {
                            "2024-01-15": {
                                "evap": 5.2,
                                "temp_min": 10.0,
                                "temp_max": 20.0,
                            },
                        },
                    },
                    # Missing coordinates
                    {
                        "name": "Bad Station 1",
                        "data": {
                            "2024-01-15": {
                                "evap": 5.0,
                            },
                        },
                    },
                    # Invalid evap
                    {
                        "name": "Bad Station 2",
                        "lat": 33.0,
                        "long": 35.0,
                        "data": {
                            "2024-01-15": {
                                "evap": "not_a_number",
                            },
                        },
                    },
                    # Missing evap
                    {
                        "name": "Bad Station 3",
                        "lat": 33.0,
                        "long": 35.0,
                        "data": {
                            "2024-01-15": {
                                "temp_min": 10.0,
                            },
                        },
                    },
                    # Invalid date format
                    {
                        "name": "Bad Station 4",
                        "lat": 33.0,
                        "long": 35.0,
                        "data": {
                            "invalid-date": {
                                "evap": 5.0,
                            },
                        },
                    },
                    # Another valid record (should be included)
                    {
                        "name": "Good Station 2",
                        "lat": 31.0,
                        "long": 34.0,
                        "data": {
                            "2024-01-15": {
                                "evap": 6.0,
                            },
                        },
                    },
                ],
            }
        }
    }

    points = parse_forecast_points(payload)

    # Should have 2 valid points
    assert len(points) == 2, f"Expected 2 valid points, got {len(points)}"
    assert {p.name for p in points} == {"Good Station", "Good Station 2"}


def test_parse_handles_missing_optional_fields():
    """Test parser handles missing optional fields (temps, name, area)."""
    payload = {
        "tempEvapRecord": {
            "areas": {
                "North": [
                    {
                        "lat": 32.5,
                        "long": 34.8,
                        "data": {
                            "2024-01-15": {
                                "evap": 5.2,
                                # No temp_min, temp_max
                            },
                        },
                    },
                ],
            }
        }
    }

    points = parse_forecast_points(payload)

    assert len(points) == 1
    point = points[0]
    assert point.evap_mm == 5.2
    assert point.temp_min is None
    assert point.temp_max is None
    assert point.name is None
    assert point.geographic_area == "North"


def test_parse_empty_payload():
    """Test parser handles empty or missing payload gracefully."""
    # Empty tempEvapRecord
    payload1 = {"tempEvapRecord": {}}
    points1 = parse_forecast_points(payload1)
    assert points1 == []

    # Missing tempEvapRecord
    payload2 = {}
    points2 = parse_forecast_points(payload2)
    assert points2 == []

    # Missing areas
    payload3 = {"tempEvapRecord": {"areas": {}}}
    points3 = parse_forecast_points(payload3)
    assert points3 == []


def test_parse_invalid_temp_values():
    """Test parser handles invalid temp values gracefully (temps are optional)."""
    payload = {
        "tempEvapRecord": {
            "areas": {
                "North": [
                    {
                        "name": "Station A",
                        "lat": 32.5,
                        "long": 34.8,
                        "data": {
                            "2024-01-15": {
                                "evap": 5.2,
                                "temp_min": "invalid",
                                "temp_max": None,
                            },
                        },
                    },
                ],
            }
        }
    }

    points = parse_forecast_points(payload)

    assert len(points) == 1
    point = points[0]
    assert point.evap_mm == 5.2
    # Invalid temps should be None
    assert point.temp_min is None
    assert point.temp_max is None

