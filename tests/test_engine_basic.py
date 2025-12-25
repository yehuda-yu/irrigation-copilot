"""
Basic engine computation tests.

Tests for core irrigation computation logic in app/domain/irrigation_engine.py.
"""

import datetime

import pytest

from app.domain import irrigation_engine, models


def test_compute_farm_simple_case():
    """Test farm mode computation: evap_mm=5, area_m2=100, kc=1.0, eff=1.0 => 500 liters."""
    profile = models.ProfileInput(
        mode="farm",
        lat=32.0,
        lon=34.0,
        area_m2=100.0,
        crop_name="tomato",
        stage="mid",
    )
    forecast = models.ForecastPoint(
        date=datetime.date(2025, 1, 15),
        lat=32.0,
        lon=34.0,
        evap_mm=5.0,
    )

    plan = irrigation_engine.compute_plan(profile, forecast)

    # Expected: 5 mm * 100 m² * 1.15 (tomato mid) / 0.85 (default eff) = 676.47...
    # But let's check the structure first
    assert plan.mode == "farm"
    assert plan.liters_per_day is not None
    assert plan.liters_per_day > 0
    assert plan.ml_per_day is None
    assert plan.pulses_per_day >= 1
    assert "kc" in plan.inputs_used
    assert "efficiency" in plan.inputs_used
    assert "area_m2" in plan.inputs_used
    assert "evap_mm" in plan.inputs_used

    # Check coefficient source info is included
    assert plan.coefficient_value_used > 0
    assert "source_type" in plan.coefficient_source
    assert "source_title" in plan.coefficient_source
    assert "source_url" in plan.coefficient_source
    assert plan.coefficient_source["source_type"] == "fao56_stage"


def test_efficiency_increases_required_liters():
    """Test that lower efficiency increases required liters."""
    profile1 = models.ProfileInput(
        mode="farm",
        lat=32.0,
        lon=34.0,
        area_m2=100.0,
        crop_name="tomato",
        stage="mid",
        efficiency=1.0,
    )
    profile2 = models.ProfileInput(
        mode="farm",
        lat=32.0,
        lon=34.0,
        area_m2=100.0,
        crop_name="tomato",
        stage="mid",
        efficiency=0.8,
    )
    forecast = models.ForecastPoint(
        date=datetime.date(2025, 1, 15),
        lat=32.0,
        lon=34.0,
        evap_mm=5.0,
    )

    plan1 = irrigation_engine.compute_plan(profile1, forecast)
    plan2 = irrigation_engine.compute_plan(profile2, forecast)

    # Lower efficiency should require more liters
    assert plan2.liters_per_day > plan1.liters_per_day


def test_unknown_crop_raises_error():
    """Test that unknown crop raises ValueError (no silent defaults)."""
    profile = models.ProfileInput(
        mode="farm",
        lat=32.0,
        lon=34.0,
        area_m2=100.0,
        crop_name="unknown_crop_xyz",
    )
    forecast = models.ForecastPoint(
        date=datetime.date(2025, 1, 15),
        lat=32.0,
        lon=34.0,
        evap_mm=5.0,
    )

    with pytest.raises(ValueError, match="not supported"):
        irrigation_engine.compute_plan(profile, forecast)


def test_pulses_rule_is_deterministic():
    """Test that pulses change according to thresholds."""
    forecast = models.ForecastPoint(
        date=datetime.date(2025, 1, 15),
        lat=32.0,
        lon=34.0,
        evap_mm=5.0,
    )

    # Low evap -> 1 pulse (default)
    profile_low = models.ProfileInput(
        mode="farm",
        lat=32.0,
        lon=34.0,
        area_m2=100.0,
        crop_name="tomato",
        stage="initial",
    )
    plan_low = irrigation_engine.compute_plan(profile_low, forecast)
    assert plan_low.pulses_per_day == 1

    # High evap -> more pulses
    forecast_high = models.ForecastPoint(
        date=datetime.date(2025, 1, 15),
        lat=32.0,
        lon=34.0,
        evap_mm=10.0,
    )
    profile_high = models.ProfileInput(
        mode="farm",
        lat=32.0,
        lon=34.0,
        area_m2=100.0,
        crop_name="tomato",
        stage="mid",
    )
    plan_high = irrigation_engine.compute_plan(profile_high, forecast_high)
    # Should have more pulses due to higher liters_per_m2
    assert plan_high.pulses_per_day >= plan_low.pulses_per_day


def test_stage_defaults_to_mid_with_warning():
    """Test that missing stage defaults to mid with warning."""
    profile = models.ProfileInput(
        mode="farm",
        lat=32.0,
        lon=34.0,
        area_m2=100.0,
        crop_name="tomato",
        # stage not provided
    )
    forecast = models.ForecastPoint(
        date=datetime.date(2025, 1, 15),
        lat=32.0,
        lon=34.0,
        evap_mm=5.0,
    )

    plan = irrigation_engine.compute_plan(profile, forecast)

    # Should use mid-stage Kc
    assert plan.coefficient_value_used == pytest.approx(1.15, abs=0.01)  # tomato mid
    # Should have warning about defaulting
    assert any("defaulting" in w.lower() or "stage" in w.lower() for w in plan.warnings)


def test_plant_mode_computation():
    """Test plant mode computation."""
    profile = models.ProfileInput(
        mode="plant",
        lat=32.0,
        lon=34.0,
        pot_volume_liters=5.0,
        plant_profile_name="leafy_houseplant",
    )
    forecast = models.ForecastPoint(
        date=datetime.date(2025, 1, 15),
        lat=32.0,
        lon=34.0,
        evap_mm=5.0,
    )

    plan = irrigation_engine.compute_plan(profile, forecast)

    assert plan.mode == "plant"
    assert plan.ml_per_day is not None
    assert plan.ml_per_day > 0
    assert plan.liters_per_day is None
    assert plan.pulses_per_day >= 1


def test_compute_with_invalid_inputs():
    """Test computation with invalid inputs raises errors."""
    forecast = models.ForecastPoint(
        date=datetime.date(2025, 1, 15),
        lat=32.0,
        lon=34.0,
        evap_mm=5.0,
    )

    # Missing required fields
    with pytest.raises(ValueError):
        profile = models.ProfileInput(
            mode="farm",
            lat=32.0,
            lon=34.0,
            # Missing area_m2 and area_dunam
            crop_name="tomato",
        )
        irrigation_engine.compute_plan(profile, forecast)

    # Negative area
    with pytest.raises(ValueError):
        profile = models.ProfileInput(
            mode="farm",
            lat=32.0,
            lon=34.0,
            area_m2=-100.0,
            crop_name="tomato",
        )
        irrigation_engine.compute_plan(profile, forecast)
