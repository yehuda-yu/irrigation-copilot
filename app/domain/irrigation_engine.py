"""
Pure irrigation computation engine.

Deterministic math only: no I/O, no network, no LLM calls.
Core formula: liters = evap_mm * area_m2 * Kc / efficiency
"""

from app.domain import kc_catalog, models, units


def compute_plan(
    profile: models.ProfileInput, forecast: models.ForecastPoint
) -> models.IrrigationPlan:
    """
    Compute irrigation plan from profile and forecast.

    Core formula:
        base_liters = evap_mm * area_m2 * kc
        liters_per_day = base_liters / efficiency

    Args:
        profile: User profile (mode, location, area/crop/plant info)
        forecast: Forecast point with evaporation data

    Returns:
        Computed IrrigationPlan with daily recommendations

    Raises:
        ValueError: If inputs are invalid (negative area, etc.)
    """
    warnings: list[str] = []
    kc_source_info: kc_catalog.CoefficientSourceInfo | None = None

    # Resolve area
    area_m2: float
    if profile.mode == "farm":
        if profile.area_m2 is not None:
            area_m2 = profile.area_m2
        elif profile.area_dunam is not None:
            area_m2 = units.dunam_to_m2(profile.area_dunam)
        else:
            raise ValueError("Farm mode requires area_m2 or area_dunam")

        if area_m2 <= 0:
            raise ValueError(f"Area must be positive, got {area_m2} m²")

        # Resolve Kc (FAO-56 stage-based)
        crop_name = profile.crop_name or ""
        stage = profile.stage

        # Default to "mid" if stage not provided (user-friendly)
        if not stage:
            stage = "mid"
            warnings.append(
                "Stage not provided, defaulting to 'mid'. "
                "Provide stage (initial/mid/late) for more accurate results."
            )

        try:
            kc = kc_catalog.get_kc_stage(crop_name, stage)
            kc_source_info = kc_catalog.get_crop_source_info(crop_name)
        except kc_catalog.UnknownCropError as e:
            warnings.append(
                f"Unknown crop '{crop_name}': {str(e)}. "
                "Cannot compute irrigation plan without coefficient data."
            )
            raise ValueError(
                f"Crop '{crop_name}' is not supported. "
                f"Available crops: {', '.join(kc_catalog.list_available_crops())}"
            ) from e
        except ValueError as e:
            # Invalid stage or other validation error
            warnings.append(f"Kc lookup error: {str(e)}")
            raise ValueError(str(e)) from e

    else:  # plant mode
        # For plant mode, estimate effective area from pot volume
        # Simple heuristic: assume pot is roughly cylindrical
        # Volume = π * r² * h, but we simplify: use pot_volume as proxy for area
        # More accurate: if we have diameter, compute area; otherwise use volume-based estimate
        if profile.pot_volume_liters is not None:
            # Heuristic: 1 liter pot ≈ 0.01 m² effective area (rough approximation)
            # This is a simplified model; in reality, pot shape and plant size matter
            area_m2 = profile.pot_volume_liters * 0.01
        elif profile.pot_diameter_cm is not None:
            # Calculate area from diameter: π * (d/2)²
            import math

            radius_m = (profile.pot_diameter_cm / 100.0) / 2.0
            area_m2 = math.pi * radius_m * radius_m
        else:
            raise ValueError("Plant mode requires pot_volume_liters or pot_diameter_cm")

        if area_m2 <= 0:
            raise ValueError(f"Pot size must be positive, got area_m2={area_m2}")

        # Resolve Kc (plant profiles use simple lookup)
        profile_name = profile.plant_profile_name or ""
        try:
            kc = kc_catalog.get_plant_kc(profile_name)
            kc_source_info = kc_catalog.get_plant_source_info(profile_name)
        except kc_catalog.UnknownCropError as e:
            warnings.append(
                f"Unknown plant profile '{profile_name}': {str(e)}. "
                "Cannot compute irrigation plan without coefficient data."
            )
            raise ValueError(
                f"Plant profile '{profile_name}' is not supported. "
                f"Available profiles: {', '.join(kc_catalog.list_available_plant_profiles())}"
            ) from e

    # Resolve efficiency
    if profile.efficiency is not None:
        efficiency = profile.efficiency
    else:
        # Default efficiency by method
        method = (profile.irrigation_method or "").lower()
        if method == "drip":
            efficiency = 0.9
        elif method == "sprinkler":
            efficiency = 0.75
        else:
            # Default: 0.85 for farm, 1.0 for plant (manual watering)
            efficiency = 0.85 if profile.mode == "farm" else 1.0

    if efficiency <= 0 or efficiency > 1:
        raise ValueError(f"Efficiency must be in (0, 1], got {efficiency}")

    # Compute water need
    # base_liters = evap_mm * area_m2 * kc
    # liters_per_day = base_liters / efficiency
    base_liters = units.mm_to_liters(forecast.evap_mm * kc, area_m2)
    liters_per_day = max(0.0, base_liters / efficiency)

    # Compute pulses (recommendation only - default 1)
    # Only suggest 2+ if source explicitly suggests splitting OR very conservative heuristic
    pulses_per_day: int = 1
    pulse_warning: str | None = None

    if profile.mode == "farm":
        # Check if source suggests splitting (for future: read from coefficient metadata)
        # For MVP: very conservative heuristic only
        liters_per_m2 = liters_per_day / area_m2 if area_m2 > 0 else 0
        if liters_per_m2 > 10:  # Very high water requirement
            pulses_per_day = 2
            pulse_warning = (
                "High water requirement detected. Consider splitting irrigation. "
                "Verify with agronomist based on soil type and irrigation system."
            )
    else:  # plant mode
        # For plants: default 1, only suggest 2 if outdoor and very high evap
        if profile.indoor_outdoor == "outdoor" and forecast.evap_mm > 8:
            pulses_per_day = 2
            pulse_warning = (
                "High evaporation detected for outdoor plant. "
                "Consider morning and evening watering. "
                "Verify based on plant type and pot size."
            )

    if pulse_warning:
        warnings.append(pulse_warning)

    # Build inputs_used dict
    inputs_used: dict[str, float | str] = {
        "kc": kc,
        "efficiency": efficiency,
        "area_m2": area_m2,
        "evap_mm": forecast.evap_mm,
    }

    # Get coefficient source info
    if kc_source_info:
        coefficient_source_info = kc_source_info.to_dict()
    else:
        # Fallback if source info unavailable
        coefficient_source_info = {
            "source_type": "unknown",
            "source_title": "Unknown",
            "source_url": "",
            "table_reference": None,
        }

    # Build output
    if profile.mode == "farm":
        liters_per_dunam = (liters_per_day / area_m2) * 1000.0 if area_m2 > 0 else 0.0
        return models.IrrigationPlan(
            date=forecast.date,
            mode="farm",
            liters_per_day=liters_per_day,
            liters_per_dunam=liters_per_dunam,
            ml_per_day=None,
            pulses_per_day=pulses_per_day,
            inputs_used=inputs_used,
            coefficient_value_used=kc,
            coefficient_source=coefficient_source_info,
            warnings=warnings,
        )
    else:  # plant mode
        ml_per_day = units.liters_to_ml(liters_per_day)
        return models.IrrigationPlan(
            date=forecast.date,
            mode="plant",
            liters_per_day=None,
            liters_per_dunam=None,
            ml_per_day=ml_per_day,
            pulses_per_day=pulses_per_day,
            inputs_used=inputs_used,
            coefficient_value_used=kc,
            coefficient_source=coefficient_source_info,
            warnings=warnings,
        )
