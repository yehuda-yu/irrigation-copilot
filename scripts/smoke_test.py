"""
Smoke test for environment verification.

Imports main packages and verifies basic functionality without network calls.
Run with: uv run python scripts/smoke_test.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def smoke_test():
    """Run smoke tests on main packages."""
    errors = []

    # Test domain models
    try:
        from app.domain.models import ForecastPoint, IrrigationPlan, ProfileInput

        # Verify models can be instantiated
        _ = ProfileInput, ForecastPoint, IrrigationPlan
        print("[OK] Domain models import")
    except Exception as e:
        errors.append(f"Domain models: {e}")

    # Test unit conversions
    try:
        from app.domain.units import dunam_to_m2, m2_to_dunam, mm_to_liters

        # Quick sanity check
        assert mm_to_liters(1.0, 1.0) == 1.0
        assert dunam_to_m2(1.0) == 1000.0
        assert m2_to_dunam(1000.0) == 1.0
        print("[OK] Unit conversions")
    except Exception as e:
        errors.append(f"Unit conversions: {e}")

    # Test API setup
    try:
        from app.api.main import app

        assert app is not None
        print("[OK] FastAPI app import")
    except Exception as e:
        errors.append(f"FastAPI app: {e}")

    # Test config
    try:
        from app.utils.config import settings

        assert settings is not None
        print("[OK] Config settings")
    except Exception as e:
        errors.append(f"Config: {e}")

    if errors:
        print("\n[ERROR] Issues found:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("\n[SUCCESS] All smoke tests passed!")


if __name__ == "__main__":
    smoke_test()
