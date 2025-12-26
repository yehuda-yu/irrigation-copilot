"""
Crop coefficient (Kc) catalog.

Maps crop/plant types to Kc values for irrigation calculations.
Loads FAO-56 stage-based coefficients from data/coefficients/*.json files.

All coefficients based on ET0 Penman-Monteith reference.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Path to coefficients data directory (relative to project root)
_COEFFICIENTS_DIR = Path(__file__).parent.parent.parent / "data" / "coefficients"

# In-memory cache of loaded coefficients
_CROP_CATALOG_CACHE: dict[str, dict[str, Any]] | None = None
_PLANT_CATALOG_CACHE: dict[str, float] | None = None


def _load_crop_coefficients() -> dict[str, dict[str, Any]]:
    """
    Load crop coefficients from JSON files in data/coefficients/.

    Returns:
        Dictionary mapping crop names to coefficient data structures
    """
    global _CROP_CATALOG_CACHE
    if _CROP_CATALOG_CACHE is not None:
        return _CROP_CATALOG_CACHE

    catalog: dict[str, dict[str, Any]] = {}

    if not _COEFFICIENTS_DIR.exists():
        logger.warning(
            f"Coefficients directory not found: {_COEFFICIENTS_DIR}. "
            "No crop coefficients available."
        )
        _CROP_CATALOG_CACHE = catalog
        return catalog

    # Load all JSON files in coefficients directory
    for json_file in _COEFFICIENTS_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                profile_type = data.get("profile_type", "").lower().strip()
                # Only load crops (not plant profiles)
                if profile_type != "plant":
                    crop_name = data.get("crop_name", "").lower().strip()
                    if crop_name:
                        catalog[crop_name] = data
                    else:
                        logger.warning(f"JSON file {json_file} missing 'crop_name' field")
        except Exception as e:
            logger.error(f"Failed to load coefficient file {json_file}: {e}")

    _CROP_CATALOG_CACHE = catalog
    logger.info(f"Loaded {len(catalog)} crop coefficient files")
    return catalog


def _load_plant_coefficients() -> dict[str, dict[str, Any]]:
    """
    Load plant profile coefficients from JSON files in data/coefficients/.

    Returns:
        Dictionary mapping plant profile names to coefficient data structures
    """
    global _PLANT_CATALOG_CACHE
    if _PLANT_CATALOG_CACHE is not None:
        return _PLANT_CATALOG_CACHE

    catalog: dict[str, dict[str, Any]] = {}

    if not _COEFFICIENTS_DIR.exists():
        logger.warning(
            f"Coefficients directory not found: {_COEFFICIENTS_DIR}. "
            "No plant profile coefficients available."
        )
        _PLANT_CATALOG_CACHE = catalog
        return catalog

    # Load all JSON files in coefficients directory
    for json_file in _COEFFICIENTS_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                profile_type = data.get("profile_type", "").lower().strip()
                # Only load plant profiles (not crops)
                if profile_type == "plant":
                    crop_name = data.get("crop_name", "").lower().strip()
                    if crop_name:
                        catalog[crop_name] = data
                    else:
                        logger.warning(f"JSON file {json_file} missing 'crop_name' field")
        except Exception as e:
            logger.error(f"Failed to load coefficient file {json_file}: {e}")

    _PLANT_CATALOG_CACHE = catalog
    logger.info(f"Loaded {len(catalog)} plant profile coefficient files")
    return catalog


class UnknownCropError(ValueError):
    """Raised when a crop is not found in the catalog."""

    pass


class CoefficientSourceInfo:
    """Information about the coefficient source used."""

    def __init__(
        self,
        kc_value: float,
        source_type: str,
        source_title: str,
        source_url: str,
        table_reference: str | None = None,
    ):
        self.kc_value = kc_value
        self.source_type = source_type
        self.source_title = source_title
        self.source_url = source_url
        self.table_reference = table_reference

    def to_dict(self) -> dict[str, str | None]:
        """Convert to dictionary for output."""
        return {
            "source_type": self.source_type,
            "source_title": self.source_title,
            "source_url": self.source_url,
            "table_reference": self.table_reference,
        }


def get_kc_stage(crop_name: str, stage: str) -> float:
    """
    Get Kc value for a crop and stage.

    Args:
        crop_name: Crop name (case-insensitive)
        stage: Stage ("initial", "mid", "late")

    Returns:
        Kc coefficient value

    Raises:
        UnknownCropError: If crop is not found in catalog
        ValueError: If stage is invalid
    """
    crop_key = crop_name.lower().strip()
    catalog = _load_crop_coefficients()
    crop_data = catalog.get(crop_key)

    if crop_data is None:
        raise UnknownCropError(
            f"Crop '{crop_name}' not found in catalog. "
            f"Available crops: {', '.join(sorted(catalog.keys()))}"
        )

    coeff_data = crop_data.get("coefficients", {})
    coeff_type = coeff_data.get("type", "stage")

    if coeff_type != "stage":
        raise ValueError(
            f"Crop '{crop_name}' has unsupported coefficient type '{coeff_type}'. "
            "Only stage-based coefficients are supported."
        )

    # Map stage to kc field
    stage_lower = stage.lower().strip()
    stage_map = {
        "initial": "kc_initial",
        "mid": "kc_mid",
        "late": "kc_end",
    }

    if stage_lower not in stage_map:
        raise ValueError(
            f"Invalid stage '{stage}'. Allowed stages: {', '.join(stage_map.keys())}"
        )

    kc_field = stage_map[stage_lower]
    kc_value = coeff_data.get(kc_field)

    if kc_value is None:
        raise ValueError(
            f"Crop '{crop_name}' has no coefficient for stage '{stage}'. "
            f"Available fields: {list(coeff_data.keys())}"
        )

    return float(kc_value)


def get_crop_source_info(crop_name: str) -> CoefficientSourceInfo | None:
    """
    Get source information for a crop.

    Args:
        crop_name: Crop name (case-insensitive)

    Returns:
        CoefficientSourceInfo or None if crop not found
    """
    crop_key = crop_name.lower().strip()
    catalog = _load_crop_coefficients()
    crop_data = catalog.get(crop_key)

    if crop_data is None:
        return None

    metadata = crop_data.get("metadata", {})
    source = metadata.get("source", {})

    return CoefficientSourceInfo(
        kc_value=0.0,  # Not used in source info
        source_type="fao56_stage",
        source_title=source.get("title", "FAO-56 Table 12"),
        source_url=source.get("url", "https://www.fao.org/4/x0490e/x0490e0b.htm"),
        table_reference=source.get("table", "Table 12"),
    )


def get_plant_source_info(profile_name: str) -> CoefficientSourceInfo | None:
    """
    Get source information for a plant profile.

    Args:
        profile_name: Plant profile name (case-insensitive)

    Returns:
        CoefficientSourceInfo or None if profile not found
    """
    profile_key = profile_name.lower().strip()
    catalog = _load_plant_coefficients()
    profile_data = catalog.get(profile_key)

    if profile_data is None:
        return None

    metadata = profile_data.get("metadata", {})
    source = metadata.get("source", {})

    return CoefficientSourceInfo(
        kc_value=0.0,  # Not used in source info
        source_type="plant_profile",
        source_title=source.get("title", "MVP Estimate"),
        source_url=source.get("url", ""),
        table_reference=source.get("table"),
    )


def get_plant_kc(profile_name: str) -> float:
    """
    Get Kc value for a plant profile.

    Args:
        profile_name: Plant profile name (case-insensitive)

    Returns:
        Kc coefficient value

    Raises:
        UnknownCropError: If profile is not found in catalog (no silent defaults)
        ValueError: If coefficient data is invalid
    """
    profile_key = profile_name.lower().strip()
    catalog = _load_plant_coefficients()
    profile_data = catalog.get(profile_key)

    if profile_data is None:
        raise UnknownCropError(
            f"Plant profile '{profile_name}' not found in catalog. "
            f"Available profiles: {', '.join(sorted(catalog.keys()))}"
        )

    coeff_data = profile_data.get("coefficients", {})
    coeff_type = coeff_data.get("type", "single")

    if coeff_type != "single":
        raise ValueError(
            f"Plant profile '{profile_name}' has unsupported coefficient type '{coeff_type}'. "
            "Only single-value coefficients are supported for plant profiles."
        )

    kc_value = coeff_data.get("kc_value")
    if kc_value is None:
        raise ValueError(
            f"Plant profile '{profile_name}' has no 'kc_value' field. "
            f"Available fields: {list(coeff_data.keys())}"
        )

    return float(kc_value)


def is_crop_known(crop_name: str) -> bool:
    """
    Check if a crop name is in the catalog.

    Args:
        crop_name: Crop name (case-insensitive)

    Returns:
        True if crop is known, False otherwise
    """
    crop_key = crop_name.lower().strip()
    catalog = _load_crop_coefficients()
    return crop_key in catalog


def is_plant_profile_known(profile_name: str) -> bool:
    """
    Check if a plant profile name is in the catalog.

    Args:
        profile_name: Plant profile name (case-insensitive)

    Returns:
        True if profile is known, False otherwise
    """
    profile_key = profile_name.lower().strip()
    catalog = _load_plant_coefficients()
    return profile_key in catalog


def list_available_crops() -> list[str]:
    """
    List all available crop types in catalog.

    Returns:
        List of crop type identifiers
    """
    catalog = _load_crop_coefficients()
    return sorted(catalog.keys())


def list_available_plant_profiles() -> list[str]:
    """
    List all available plant profile names in catalog.

    Returns:
        List of plant profile identifiers
    """
    catalog = _load_plant_coefficients()
    return sorted(catalog.keys())


# Legacy function for backward compatibility
def get_crop_kc(crop_name: str, stage: str | None = None) -> float:
    """
    Get Kc value for a crop, optionally by stage (legacy function).

    Args:
        crop_name: Crop name (case-insensitive)
        stage: Stage ("initial", "mid", "late") - defaults to "mid" if not provided

    Returns:
        Kc coefficient value

    Raises:
        UnknownCropError: If crop is not found in catalog
        ValueError: If stage is invalid
    """
    if stage is None:
        stage = "mid"
    return get_kc_stage(crop_name, stage)
