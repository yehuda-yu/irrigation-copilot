"""
Unit conversion helpers.

Pure functions for converting between units (mm, cm, liters, dunam, etc.).
Used by domain engine and data adapters.
"""


def mm_to_liters(mm: float, area_m2: float) -> float:
    """
    Convert mm of water to liters for given area.

    Formula: 1 mm * 1 m² = 1 liter

    Args:
        mm: Depth in millimeters (must be >= 0)
        area_m2: Area in square meters (must be >= 0)

    Returns:
        Volume in liters

    Raises:
        ValueError: If inputs are negative
    """
    if mm < 0:
        raise ValueError(f"mm must be non-negative, got {mm}")
    if area_m2 < 0:
        raise ValueError(f"area_m2 must be non-negative, got {area_m2}")
    return mm * area_m2


def dunam_to_m2(dunam: float) -> float:
    """
    Convert dunam to square meters.

    Args:
        dunam: Area in dunams (must be >= 0)

    Returns:
        Area in square meters (1 dunam = 1000 m²)

    Raises:
        ValueError: If input is negative
    """
    if dunam < 0:
        raise ValueError(f"dunam must be non-negative, got {dunam}")
    return dunam * 1000.0


def m2_to_dunam(m2: float) -> float:
    """
    Convert square meters to dunams.

    Args:
        m2: Area in square meters

    Returns:
        Area in dunams
    """
    # TODO: Implement conversion
    return m2 / 1000.0


def liters_to_ml(liters: float) -> float:
    """
    Convert liters to milliliters.

    Args:
        liters: Volume in liters (must be >= 0)

    Returns:
        Volume in milliliters

    Raises:
        ValueError: If input is negative
    """
    if liters < 0:
        raise ValueError(f"liters must be non-negative, got {liters}")
    return liters * 1000.0


def liters_per_dunam_to_mm_per_day(liters_per_dunam: float) -> float:
    """
    Convert liters per dunam to mm per day.

    Args:
        liters_per_dunam: Irrigation rate in liters/dunam (must be >= 0)

    Returns:
        Equivalent depth in mm/day

    Raises:
        ValueError: If input is negative
    """
    if liters_per_dunam < 0:
        raise ValueError(f"liters_per_dunam must be non-negative, got {liters_per_dunam}")
    # 1 dunam = 1000 m², 1 mm * 1 m² = 1 liter
    # So liters_per_dunam / 1000 = mm_per_day
    return liters_per_dunam / 1000.0
