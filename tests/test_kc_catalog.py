"""
Tests for Kc catalog loading and lookup.

Tests that coefficient files load correctly and values match FAO-56 sources.
"""

import json
from pathlib import Path

import pytest

from app.domain import kc_catalog


def test_load_crop_coefficients():
    """Test that crop coefficient files load successfully."""
    catalog = kc_catalog._load_crop_coefficients()
    assert isinstance(catalog, dict)
    assert len(catalog) > 0

    # Check that known crops are loaded
    assert "tomato" in catalog
    assert "pepper" in catalog
    assert "avocado" in catalog
    assert "citrus" in catalog
    assert "cucumber" in catalog


def test_get_kc_stage_known_crop():
    """Test getting Kc for a known crop and stage."""
    kc = kc_catalog.get_kc_stage("tomato", "mid")
    assert isinstance(kc, float)
    assert kc > 0
    assert kc <= 2.0  # Reasonable range


def test_get_kc_stage_unknown_crop():
    """Test that unknown crop raises UnknownCropError."""
    with pytest.raises(kc_catalog.UnknownCropError):
        kc_catalog.get_kc_stage("nonexistent_crop_xyz", "mid")


def test_get_kc_stage_invalid_stage():
    """Test that invalid stage raises ValueError."""
    with pytest.raises(ValueError, match="Invalid stage"):
        kc_catalog.get_kc_stage("tomato", "invalid_stage")

    # Should list allowed stages
    with pytest.raises(ValueError, match="initial.*mid.*late"):
        kc_catalog.get_kc_stage("tomato", "wrong")


def test_get_kc_stage_all_stages():
    """Test that all stages return different values for tomato."""
    kc_initial = kc_catalog.get_kc_stage("tomato", "initial")
    kc_mid = kc_catalog.get_kc_stage("tomato", "mid")
    kc_late = kc_catalog.get_kc_stage("tomato", "late")

    assert kc_initial != kc_mid or kc_mid != kc_late  # At least one should differ
    assert kc_mid > kc_initial  # Mid-season typically highest


def test_spot_check_tomato_values():
    """Spot-check tomato Kc values against FAO-56 Table 12."""
    # FAO-56 Table 12: tomato Kc_ini=0.6, Kc_mid=1.15, Kc_end=0.9
    kc_initial = kc_catalog.get_kc_stage("tomato", "initial")
    kc_mid = kc_catalog.get_kc_stage("tomato", "mid")
    kc_late = kc_catalog.get_kc_stage("tomato", "late")

    # Allow small tolerance for rounding
    assert abs(kc_initial - 0.6) < 0.01
    assert abs(kc_mid - 1.15) < 0.01
    assert abs(kc_late - 0.9) < 0.01


def test_spot_check_pepper_values():
    """Spot-check pepper Kc values against FAO-56 Table 12."""
    # FAO-56 Table 12: pepper Kc_ini=0.6, Kc_mid=1.05, Kc_end=0.9
    kc_initial = kc_catalog.get_kc_stage("pepper", "initial")
    kc_mid = kc_catalog.get_kc_stage("pepper", "mid")
    kc_late = kc_catalog.get_kc_stage("pepper", "late")

    assert abs(kc_initial - 0.6) < 0.01
    assert abs(kc_mid - 1.05) < 0.01
    assert abs(kc_late - 0.9) < 0.01


def test_spot_check_avocado_values():
    """Spot-check avocado Kc values against FAO-56 Table 12."""
    # FAO-56 Table 12: avocado Kc_ini=0.65, Kc_mid=0.95, Kc_end=0.75
    kc_initial = kc_catalog.get_kc_stage("avocado", "initial")
    kc_mid = kc_catalog.get_kc_stage("avocado", "mid")
    kc_late = kc_catalog.get_kc_stage("avocado", "late")

    assert abs(kc_initial - 0.65) < 0.01
    assert abs(kc_mid - 0.95) < 0.01
    assert abs(kc_late - 0.75) < 0.01


def test_coefficient_file_structure():
    """Test that coefficient files have required FAO-only structure."""
    coeff_dir = Path(__file__).parent.parent / "data" / "coefficients"
    for json_file in coeff_dir.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check required fields
        assert "crop_name" in data
        assert "coefficients" in data
        assert "metadata" in data

        # Check coefficients structure (FAO-only)
        coeff = data["coefficients"]
        assert coeff["type"] == "stage"
        assert coeff["basis"] == "ET0 Penman-Monteith"
        assert "kc_initial" in coeff
        assert "kc_mid" in coeff
        assert "kc_end" in coeff

        # Check metadata has source
        metadata = data["metadata"]
        assert "source" in metadata
        source = metadata["source"]
        assert "title" in source
        assert "url" in source
        assert "FAO-56" in source["title"] or "fao" in source["title"].lower()


def test_is_crop_known():
    """Test is_crop_known function."""
    assert kc_catalog.is_crop_known("tomato")
    assert kc_catalog.is_crop_known("pepper")
    assert not kc_catalog.is_crop_known("nonexistent_crop")


def test_list_available_crops():
    """Test list_available_crops function."""
    crops = kc_catalog.list_available_crops()
    assert isinstance(crops, list)
    assert len(crops) > 0
    assert "tomato" in crops
    assert "pepper" in crops
    assert all(isinstance(c, str) for c in crops)


def test_get_crop_source_info():
    """Test getting source information for a crop."""
    source_info = kc_catalog.get_crop_source_info("tomato")
    assert source_info is not None
    assert source_info.source_type == "fao56_stage"
    assert "FAO-56" in source_info.source_title
    assert source_info.source_url.startswith("https://www.fao.org")

    # Unknown crop should return None
    assert kc_catalog.get_crop_source_info("nonexistent") is None


def test_get_crop_kc_legacy_defaults_to_mid():
    """Test legacy get_crop_kc function defaults to mid if stage not provided."""
    kc_mid = kc_catalog.get_kc_stage("tomato", "mid")
    kc_no_stage = kc_catalog.get_crop_kc("tomato")
    assert kc_no_stage == kc_mid

    # With stage, should match
    kc_with_stage = kc_catalog.get_crop_kc("tomato", "initial")
    assert kc_with_stage == kc_catalog.get_kc_stage("tomato", "initial")


def test_coefficient_source_info_structure():
    """Test that CoefficientSourceInfo has correct structure."""
    source_info = kc_catalog.get_crop_source_info("tomato")
    assert source_info is not None

    # Check structure
    assert hasattr(source_info, "kc_value")
    assert hasattr(source_info, "source_type")
    assert hasattr(source_info, "source_title")
    assert hasattr(source_info, "source_url")
    assert hasattr(source_info, "table_reference")

    # Check to_dict
    info_dict = source_info.to_dict()
    assert "source_type" in info_dict
    assert "source_title" in info_dict
    assert "source_url" in info_dict
    assert "table_reference" in info_dict
