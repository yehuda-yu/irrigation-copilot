# Project Status

**Doc conventions:** This file reflects the current snapshot status only. For historical timeline and decisions, see `PROJECT_JOURNAL.md`.

## Current Phase
Phase 4: Nearest point selection (geospatial matching) - Complete

## Done
- Project structure scaffolded with strict domain/data separation
- UV project setup configured with quality gates (ruff check, pytest)
- **MoAG data adapter:**
  - SQLite cache for forecast payloads (app/storage/cache.py)
  - MoAG API client with retries and Chrome-like headers (app/data/moag_client.py)
  - Parser/normalizer for MoAG response → ForecastPoint (app/data/moag_parser.py)
  - Forecast service orchestration (app/data/forecast_service.py)
  - Centralized configuration (app/utils/config.py): cache path, MoAG timeout/retries, offline mode
  - Offline mode support (OFFLINE_MODE env var or --offline flag)
  - Manual verification script (scripts/fetch_forecast.py) with --lat/--lon support
  - Offline tests for parser and cache
- **Pure irrigation engine:**
  - Domain models (ProfileInput, IrrigationPlan) support farm/plant modes
  - Unit conversion helpers with validation (dunam_to_m2, mm_to_liters, liters_to_ml)
  - **Coefficient catalog:** FAO-56 stage-based Kc only (app/domain/kc_catalog.py)
    - Loads from `data/coefficients/*.json` files
    - Format: `kc_initial`, `kc_mid`, `kc_end` (direct fields)
    - Basis: ET0 Penman-Monteith reference evapotranspiration
    - 5 crops supported: avocado, citrus, cucumber, pepper, tomato
    - Strict unknown crop handling (raises ValueError, no silent defaults)
    - Engine defaults to "mid" stage if not provided (with warning)
  - Irrigation computation (app/domain/irrigation_engine.py):
    - Area resolution (farm: m2/dunam, plant: pot volume/diameter)
    - Kc lookup by crop name and stage
    - Efficiency defaults by irrigation method (drip: 0.9, sprinkler: 0.75, farm default: 0.85, plant default: 1.0)
    - Water need: liters = evap_mm * area_m2 * kc / efficiency
    - Pulses heuristic: default 1, suggests 2+ based on conservative thresholds
    - Output includes `coefficient_value_used` and `coefficient_source` (FAO-56 metadata)
    - Warning system for unknown crops/stages
  - Comprehensive offline tests (units, engine computation, edge cases)
- **Geospatial nearest-point selection:**
  - Haversine distance calculation with coordinate validation (app/data/station_matching.py)
  - `pick_nearest_point()` for deterministic nearest point selection
  - `get_nearest_points()` helper for k-nearest diagnostics
  - **Near-tie handling:** Epsilon tolerance (EPSILON_KM = 0.001 km = 1 meter) for floating-point comparisons
  - **Tie-breaker:** Deterministic sorting by (geographic_area, name, lat, lon) when distances are equal or within epsilon
  - **Invalid coordinates handling:**
    - User input (--lat/--lon): Strict validation, raises ValueError for out-of-range values
    - Source ForecastPoint coords: Graceful handling, skips invalid points and tracks diagnostics
    - `InvalidCoordinatesError` exception with rich diagnostics (total_points, skipped_count, skipped_points)
  - `get_selection_diagnostics()` helper for data quality assessment
  - Comprehensive offline tests (distance calculation, selection logic, near-tie scenarios, edge cases)

## Next
- Phase 5: Strands Agent MVP (integrate engine with agent tools)

## Risks
- MoAG API stability/availability
- Data normalization complexity

## Dependencies
- fastapi
- uvicorn
- pydantic
- pydantic-settings
- requests
- pytest
- ruff
- strands (agent framework)

## Configuration
- **Cache:** Default path `.cache/forecast.sqlite` (configurable via `cache_db_path` setting or env)
- **Offline mode:** Set `OFFLINE_MODE=1` env var or use `--offline` flag in scripts
- **MoAG API:** Timeout, retries, and backoff configurable via settings (defaults: 30s timeout, 3 retries, 1.0s base backoff)
