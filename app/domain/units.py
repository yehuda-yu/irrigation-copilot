"""
Unit conversion helpers.

Pure functions for converting between units (mm, cm, liters, dunam, etc.).
Used by domain engine and data adapters.
"""


def mm_to_liters(mm: float, area_m2: float) -> float:
    """
    Convert mm of water to liters for given area.
    
    Args:
        mm: Depth in millimeters
        area_m2: Area in square meters
    
    Returns:
        Volume in liters
    """
    # TODO: Implement conversion (1 mm * 1 m² = 1 liter)
    pass


def dunam_to_m2(dunam: float) -> float:
    """
    Convert dunam to square meters.
    
    Args:
        dunam: Area in dunams
    
    Returns:
        Area in square meters (1 dunam = 1000 m²)
    """
    # TODO: Implement conversion
    pass


def m2_to_dunam(m2: float) -> float:
    """
    Convert square meters to dunams.
    
    Args:
        m2: Area in square meters
    
    Returns:
        Area in dunams
    """
    # TODO: Implement conversion
    pass


def liters_per_dunam_to_mm_per_day(liters_per_dunam: float) -> float:
    """
    Convert liters per dunam to mm per day.
    
    Args:
        liters_per_dunam: Irrigation rate in liters/dunam
    
    Returns:
        Equivalent depth in mm/day
    """
    # TODO: Implement conversion
    pass

