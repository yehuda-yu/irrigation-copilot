"""
Unit conversion tests.

Tests for unit conversion functions in app/domain/units.py.
"""

import pytest

from app.domain.units import (
    dunam_to_m2,
    liters_per_dunam_to_mm_per_day,
    liters_to_ml,
    m2_to_dunam,
    mm_to_liters,
)


def test_mm_to_liters_identity():
    """Test mm to liters conversion (1 mm * 1 m² = 1 liter)."""
    assert mm_to_liters(1.0, 1.0) == 1.0
    assert mm_to_liters(5.0, 100.0) == 500.0
    assert mm_to_liters(0.0, 100.0) == 0.0
    assert mm_to_liters(10.0, 0.0) == 0.0


def test_mm_to_liters_validation():
    """Test mm_to_liters raises ValueError for negative inputs."""
    with pytest.raises(ValueError, match="mm must be non-negative"):
        mm_to_liters(-1.0, 1.0)
    with pytest.raises(ValueError, match="area_m2 must be non-negative"):
        mm_to_liters(1.0, -1.0)


def test_dunam_to_m2():
    """Test dunam to square meters conversion."""
    assert dunam_to_m2(1.0) == 1000.0
    assert dunam_to_m2(2.5) == 2500.0
    assert dunam_to_m2(0.0) == 0.0


def test_dunam_to_m2_validation():
    """Test dunam_to_m2 raises ValueError for negative input."""
    with pytest.raises(ValueError, match="dunam must be non-negative"):
        dunam_to_m2(-1.0)


def test_m2_to_dunam():
    """Test square meters to dunam conversion."""
    assert m2_to_dunam(1000.0) == 1.0
    assert m2_to_dunam(2500.0) == 2.5


def test_liters_to_ml():
    """Test liters to milliliters conversion."""
    assert liters_to_ml(1.0) == 1000.0
    assert liters_to_ml(0.5) == 500.0
    assert liters_to_ml(0.0) == 0.0
    assert liters_to_ml(2.5) == 2500.0


def test_liters_to_ml_validation():
    """Test liters_to_ml raises ValueError for negative input."""
    with pytest.raises(ValueError, match="liters must be non-negative"):
        liters_to_ml(-1.0)


def test_liters_per_dunam_to_mm_per_day():
    """Test liters per dunam to mm per day conversion."""
    assert liters_per_dunam_to_mm_per_day(1000.0) == 1.0
    assert liters_per_dunam_to_mm_per_day(5000.0) == 5.0
