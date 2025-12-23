"""
Crop coefficient (Kc) catalog.

Maps crop/plant types to Kc values for irrigation calculations.
Supports both farm crops and home plants.
"""


def get_kc(crop_type: str) -> float:
    """
    Get Kc value for crop/plant type.
    
    Args:
        crop_type: Crop or plant identifier (e.g., 'tomato', 'basil', 'lawn')
    
    Returns:
        Kc coefficient value
    
    Raises:
        KeyError: If crop type not found in catalog
    """
    # TODO: Implement catalog lookup
    pass


def list_available_crops() -> list[str]:
    """
    List all available crop/plant types in catalog.
    
    Returns:
        List of crop type identifiers
    """
    # TODO: Implement catalog listing
    pass


# Catalog data structure (to be populated)
KC_CATALOG: dict[str, float] = {
    # TODO: Populate with crop/plant Kc values
    # Example: "tomato": 1.0, "basil": 0.8, "lawn": 0.6
}

