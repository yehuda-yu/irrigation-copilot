# Project Journal

**Doc conventions:** This file is an append-only timeline of decisions, discoveries, and changes. For current status snapshot, see `01_STATUS.md`.

---

## 2025-12-23

### Initial Scaffold
- Created pure engine architecture with strict domain/data separation
- Set up Strands agent framework for MVP
- Defined core models: ProfileInput, ForecastPoint, IrrigationPlan

### Phase 1: UV + Quality Gates Setup
- Configured project for `uv` package manager
- Set up `pyproject.toml` with proper package discovery (setuptools)
- Made pandas optional dependency
- Fixed all linting issues with ruff (formatting, imports, whitespace)
- Implemented minimal unit conversion functions for testing
- Created smoke test script for environment verification
- Fixed Pydantic model issue: renamed `date` import to `Date` to avoid type annotation conflict
- All quality gates passing: `uv run ruff check .` and `uv run pytest -q`

### Phase 2: MoAG Data Adapter Implementation
- **Cache layer (app/storage/cache.py):**
  - SQLite cache storing raw payloads by date (YYYY-MM-DD)
  - Methods: `get_forecast(date)` returns Optional[dict], `set_forecast(date, payload)` stores payload
  - Auto-creates `.cache/` directory if missing
  - Fixed Windows SQLite connection handling (explicit close() to prevent file locks)
- **MoAG client (app/data/moag_client.py):**
  - `fetch_forecast_raw(date)` function with retry logic (3 attempts, exponential backoff)
  - Chrome-like headers to bypass WAF (User-Agent, Accept headers, Sec-Fetch-*)
  - Custom `MoAGClientError` exception with status code and response snippet for debugging
  - Date validation (YYYY-MM-DD format) with helpful error messages
- **Parser (app/data/moag_parser.py):**
  - `parse_forecast_points(payload)` extracts all records across areas/locations/dates
  - Handles multiple coordinate field names (lat/long, latitude/longitude, lon)
  - Skips malformed records gracefully, logs summary (total_locations_seen, total_records_emitted, skipped_records)
  - Validates required fields (evap_mm), optional fields (temp_min, temp_max, name, geographic_area)
- **Adapter orchestration (app/data/__init__.py):**
  - `get_forecast_points(date_str, cache)` single entry point
  - Cache-first strategy, falls back to stale cache if fetch fails
  - Default cache instance management
- **Testing:**
  - Offline parser tests with mocked payloads (happy path, bad records, edge cases)
  - Cache tests using temp SQLite databases
  - All tests passing, no network required
- **Scripts:**
  - `scripts/fetch_forecast.py` for manual verification (--date arg, prints summary + sample points)
- **Quality gates:** All passing (ruff check, pytest)

### Phase 2.1: Adapter Hardening and Configuration
- **Stable entrypoint:**
  - Moved `get_forecast_points()` from `app/data/__init__.py` to `app/data/forecast_service.py`
  - `__init__.py` now only re-exports for backwards compatibility
- **Centralized configuration (app/utils/config.py):**
  - Added `cache_db_path` (default: `.cache/forecast.sqlite`)
  - Added `moag_timeout_seconds`, `moag_retries`, `moag_backoff_base_seconds`
  - Added `offline_mode` boolean (reads from `OFFLINE_MODE` env var, supports 1/0, true/false)
  - Cache and client now use config values instead of hardcoded defaults
- **Offline mode:**
  - `get_forecast_points(offline_mode=True)` skips network fetch entirely
  - Raises `OfflineModeError` if cache miss occurs in offline mode
  - Script supports `--offline` flag
  - Useful for CI/CD or environments without network access
- **Network tests:**
  - Added `tests/test_moag_network.py` with `@pytest.mark.network`
  - Configured pytest to skip network tests by default (`-m "not network"`)
  - Run network tests explicitly with `pytest -m network`
- **Quality gates:** All passing (ruff check, pytest)

### Phase 3: Pure Irrigation Engine Implementation
- **Domain models (app/domain/models.py):**
  - Updated ProfileInput to support explicit farm/plant modes with mode-specific fields
  - Farm mode: area_m2/area_dunam, crop_name, stage (optional), irrigation_method
  - Plant mode: pot_volume_liters/pot_diameter_cm, plant_profile_name, indoor_outdoor
  - Added model_validator to ensure required fields per mode
  - Updated IrrigationPlan to include mode, liters_per_day (farm), ml_per_day (plant), pulses_per_day, inputs_used dict, warnings list
- **Unit conversions (app/domain/units.py):**
  - Added input validation (non-negative checks) to all conversion functions
  - Implemented liters_to_ml() helper
  - All conversions are pure, deterministic, and validated
- **Kc catalog (app/domain/kc_catalog.py):**
  - Created CROP_KC_CATALOG with 8+ crops (avocado, citrus, tomato, cucumber, grapes, wheat, corn, cotton, potato, pepper, etc.)
  - Stage-based Kc support for major crops (initial/mid/late)
  - Created PLANT_KC_CATALOG with 10 profiles (succulent, leafy_houseplant, herbs, flowering_balcony, etc.)
  - Lookup functions: get_crop_kc(crop_name, stage), get_plant_kc(profile_name)
  - Unknown crop/profile handling: returns conservative defaults (0.8 for crops, 0.5 for plants)
  - Helper functions: is_crop_known(), is_plant_profile_known(), list_available_crops(), list_available_plant_profiles()
- **Irrigation engine (app/domain/irrigation_engine.py):**
  - Implemented compute_plan(profile, forecast) -> IrrigationPlan
  - Area resolution:
    - Farm: converts dunam->m2 if needed
    - Plant: estimates effective area from pot_volume_liters (heuristic: 1L ≈ 0.01 m²) or computes from pot_diameter_cm
  - Kc resolution: looks up from catalog based on mode (crop_name+stage or plant_profile_name)
  - Efficiency resolution: uses provided value or defaults (drip: 0.9, sprinkler: 0.75, farm default: 0.85, plant default: 1.0)
  - Water need computation: base_liters = evap_mm * area_m2 * kc, liters_per_day = base_liters / efficiency
  - Pulses heuristic (deterministic):
    - Farm: 1 pulse default, 2 if liters_per_m2 > 5, 3 if > 8 (cap at 3)
    - Plant: 1 pulse default, 2 if outdoor and evap_mm > 6 (cap at 2)
  - Warning system: adds warnings for unknown crops/profiles (output still valid with defaults)
  - All logic is pure, deterministic, no I/O, no network, no LLM calls
- **Testing:**
  - Updated test_engine_units.py: added liters_to_ml tests, validation tests for all functions
  - Updated test_engine_basic.py: comprehensive tests for compute_plan()
    - test_compute_farm_simple_case: basic farm computation
    - test_efficiency_increases_required_liters: efficiency impact verification
    - test_unknown_crop_warning_and_default_kc: unknown crop handling
    - test_pulses_rule_is_deterministic: pulses threshold verification
    - test_plant_mode_computation: plant mode basic test
    - test_compute_with_invalid_inputs: error handling
  - All tests are offline, deterministic, no network required
- **Quality gates:** All passing (ruff check, pytest -q)

### Phase 3.1: Sourced Irrigation Coefficients Catalog
- **Research and source collection:**
  - Documented Israeli MoA/SHAHAM sources for 5 crops: pepper, avocado, citrus, cucumber, tomato
  - Sources include PDFs and web pages from gov.il with irrigation coefficient tables
  - Documented FAO-56 Chapter 6 Table 12 as fallback source (ET0 Penman-Monteith based)
  - Created `ai_docs/specs/coefficients_sources.md` with all sources, URLs, and metadata
- **Data model decision:**
  - Selected stage-based Kc (initial/mid/late) - Option A
  - Matches FAO-56 format, can map from Israeli time-series if needed
  - Simpler for MVP, extensible to time-series later
- **Coefficient files (data/coefficients/*.json):**
  - Created JSON files for 5 crops: pepper, avocado, citrus, cucumber, tomato
  - Each file includes: crop_name, source (primary Israeli + fallback FAO-56), coefficients, metadata
  - Source metadata includes: title, URL, type, notes, retrieved_date, status
  - Currently using FAO-56 values as fallback (needs_manual_extraction: true)
  - Files are auditable and can be updated when Israeli values are extracted
- **Catalog implementation (app/domain/kc_catalog.py):**
  - Replaced hardcoded dicts with file-based loading from data/coefficients/
  - Lazy loading with in-memory cache (loads at first access)
  - Added UnknownCropError exception (no silent defaults)
  - Updated lookup functions: get_crop_kc(), get_plant_kc() now raise on unknown
  - Added get_crop_source_info() for accessing source metadata
  - Plant profiles still use simple defaults (can be moved to files later)
- **Engine updates (app/domain/irrigation_engine.py):**
  - Updated to handle UnknownCropError: raises ValueError with helpful message
  - Removed silent default Kc behavior (unknown crops now fail explicitly)
  - Fixed pulses_per_day design:
    - Default: 1 pulse (recommendation only)
    - Only suggests 2+ if very conservative heuristic (liters_per_m2 > 10 for farm, evap_mm > 8 for outdoor plants)
    - Adds warning: "depends on soil type/system; verify with agronomist"
  - Warnings now include helpful guidance instead of just notifications
- **Evap field semantics:**
  - Documented uncertainty in ForecastPoint.evap_mm description
  - Added comments in moag_parser.py noting that exact method (Penman-Monteith, open-pan, etc.) needs verification
  - Used as ET0 proxy in calculations but semantics should be verified with MoAG
  - Action item: Contact MoAG or check documentation to verify exact method
- **Testing:**
  - Created tests/test_kc_catalog.py with 12 tests:
    - Coefficient file loading
    - Known/unknown crop handling
    - Stage-based lookup
    - Spot-checking values against FAO-56 Table 12 (tomato, pepper, avocado)
    - File structure validation
    - Source info retrieval
  - Updated test_engine_basic.py: changed unknown crop test to expect ValueError (no silent defaults)
  - All tests passing (36 passed)
- **Documentation:**
  - Created `ai_docs/specs/coefficients_sources.md` with comprehensive source documentation
  - Documented data model decision and rationale
  - Listed all Israeli sources with URLs and status
  - Documented evap field semantics uncertainty
  - Created `data/coefficients/README.md` with file format and usage notes
- **Quality gates:** All passing (ruff check, pytest -q)

### Phase 3.2: Israel-First Coefficients (Schema V2)
- **Schema V2 definition:**
  - Created `data/coefficients/SCHEMA_V2.md` with full schema documentation
  - Supports three coefficient types: `calendar_monthly`, `calendar_decadal`, `stage`
  - All coefficients must include `basis: "ET0 Penman-Monteith"`
  - Source metadata structure: `israeli` (primary) and `fao56` (fallback) with URLs, tables, extraction info
  - Updated `data/coefficients/README.md` with Schema V2 overview
- **Coefficient files updated to Schema V2:**
  - All 5 crop files (avocado, citrus, cucumber, tomato, pepper) restructured
  - Added `basis: "ET0 Penman-Monteith"` to all coefficient structures
  - Reorganized source metadata: `coefficients.source.israeli` and `coefficients.source.fao56`
  - Added extraction metadata: `extraction_required` with source URLs, expected format, crop type
  - Files ready for Israeli value extraction (currently using FAO-56 fallback)
- **Israel-first selection logic (app/domain/kc_catalog.py):**
  - Implemented `get_kc_for_date(crop, date, stage=None)` function
  - Selection priority: 1) Israeli calendar (monthly/decadal), 2) FAO stage-based, 3) UnknownCropError
  - Date-based lookup: `_get_month_from_date()` and `_get_decade_from_date()` helpers
  - Returns `CoefficientSourceInfo` with: kc_value, source_type, source_title, source_url, table_reference
  - Stage-based crops require explicit stage parameter (clear error if missing)
  - Updated `get_crop_kc()` to use `get_kc_for_date()` for backward compatibility
- **Engine updates (app/domain/irrigation_engine.py):**
  - Uses `get_kc_for_date()` with forecast date for Israel-first selection
  - Handles both calendar-based (no stage needed) and stage-based (stage required) crops
  - Includes coefficient source info in `IrrigationPlan` output
  - Added `coefficient_value_used` and `coefficient_source` fields to plan
  - Clear error messages when stage required but not provided
- **Model updates (app/domain/models.py):**
  - Added `coefficient_value_used: float` to `IrrigationPlan`
  - Added `coefficient_source: dict[str, str | None]` with source_type, source_title, source_url, table_reference
  - Updated `ForecastPoint.evap_mm` description to document ET0 Penman-Monteith basis
- **Testing:**
  - Updated `tests/test_kc_catalog.py`: 15 tests including Schema V2 validation
  - Added tests for `get_kc_for_date()`: stage-based lookup, source info structure
  - Added `test_schema_v2_validation()`: validates all coefficient files conform to schema
  - Updated `tests/test_engine_basic.py`: verify coefficient source info in plan output
  - All 39 tests passing
- **Documentation:**
  - Updated `ai_docs/specs/coefficients_sources.md`:
    - Documented Schema V2 and Israel-first selection logic
    - Confirmed ET0 Penman-Monteith basis (no longer uncertain)
    - Updated implementation status and next steps
  - Updated `data/coefficients/README.md` with Schema V2 overview
  - All code comments document ET0 Penman-Monteith basis consistently
- **Quality gates:** All passing (ruff check, pytest -q)

### Phase 3.3: Israeli Coefficient Extraction Infrastructure
- **Raw data area (data/coefficients/raw_xls/):**
  - Created directory structure for storing official .xls files
  - Added MANIFEST.md template with fields for: source URL, download date, file size, SHA256 hash
  - Documented all 5 crop source URLs:
    - avocado.xls, citrus.xls, cucumber_greenhouse.xls, tomato_structures.xls, pepper_arava_bekaa.xls
  - Added .gitkeep to ensure directory is tracked
- **Extraction dependencies:**
  - Added `extraction` optional dependency group to pyproject.toml:
    - pandas>=2.1.0 (for reading Excel)
    - xlrd>=2.0.1 (for legacy .xls files)
    - openpyxl>=3.1.0 (for .xlsx if needed)
  - Runtime app does NOT depend on these (extraction is dev-time only)
- **Extraction script (scripts/extract_israeli_coefficients.py):**
  - Command-line tool: `--crop <name>` or `--all`, `--in-dir`, `--out-dir`
  - Excel reading: Uses pandas with xlrd engine for .xls files
  - Table detection: Searches for Hebrew headers (חודש, עשרת, מקדם)
  - Value extraction:
    - Supports both monthly and decadal formats
    - Parses Hebrew month names to numbers (1-12)
    - Validates Kc range (0.1-1.5)
    - Handles variant structure (extracts "default" variant for now)
  - Output: Updates JSON files in Schema V2 format with:
    - Israeli source metadata (URL, filename, sheet, table location)
    - Extraction date and method
    - Status changed to "israeli_extracted"
    - FAO-56 kept as fallback only
- **Catalog variant support (app/domain/kc_catalog.py):**
  - Extended `get_kc_for_date()` with optional `variant` parameter
  - Variant selection logic:
    - If variant provided and exists: use it
    - Else if "default" exists: use it
    - Else: use first variant (deterministic sort)
  - Source type includes variant info: `israeli_calendar_monthly_variant_default`
  - Updated engine to pass variant=None (Phase 4 will add geospatial mapping)
- **Testing:**
  - Created `tests/test_israeli_coefficients_values.py` with 8 tests:
    - Structure validation for all 5 crops
    - Source metadata verification
    - Date-based lookup functionality
    - Variant selection logic
    - Placeholder tests for spot-checking (to be filled after extraction)
  - All tests pass (47 total tests)
- **Documentation:**
  - Updated MANIFEST.md with download instructions
  - Updated extraction script with comprehensive docstrings
  - Documented variant structure in code comments
- **Status**: Infrastructure complete. Ready for:
  1. Download .xls files from gov.il URLs
  2. Place in data/coefficients/raw_xls/
  3. Run: `uv run --extra extraction python scripts/extract_israeli_coefficients.py --all`
  4. Verify extracted values and update spot-check tests
- **Quality gates:** All passing (ruff check, pytest -q)

### Phase 3 Simplification: FAO-56 Only (MVP Decision)
- **Decision**: Simplified to FAO-56 stage-based Kc only for MVP
- **Rationale**:
  - Simpler, more maintainable for initial release
  - FAO-56 is globally recognized and well-documented
  - Stage-based approach sufficient for MVP use cases
  - Israeli calendar-based coefficients deferred to future phase
- **Coefficient data model simplification:**
  - Replaced Schema V2 with simple FAO-only structure
  - Format: `kc_initial`, `kc_mid`, `kc_end` (direct fields, no nested values)
  - Removed calendar_monthly/calendar_decadal support
  - Removed variant structure
  - All 5 crop files simplified to clean FAO format
- **Infrastructure removal:**
  - Deleted `scripts/extract_israeli_coefficients.py`
  - Deleted `data/coefficients/raw_xls/` directory and MANIFEST.md
  - Removed `extraction` optional dependency group (pandas, xlrd, openpyxl)
  - Deleted `data/coefficients/SCHEMA_V2.md`
- **Catalog simplification (app/domain/kc_catalog.py):**
  - Removed `get_kc_for_date()` and all calendar/variant logic
  - Simplified to `get_kc_stage(crop, stage)` function
  - `get_crop_source_info()` returns FAO-56 source info
  - Removed date-based lookup, variant selection, month/decade helpers
  - Kept `get_crop_kc()` as legacy wrapper (defaults to "mid")
- **Engine updates (app/domain/irrigation_engine.py):**
  - Uses `get_kc_stage()` instead of `get_kc_for_date()`
  - Defaults to "mid" stage if not provided (user-friendly)
  - Adds warning when stage defaults to mid
  - Still includes coefficient_source and coefficient_value_used in output
- **Testing:**
  - Rewrote `tests/test_kc_catalog.py` for FAO-only structure (14 tests)
  - Removed `tests/test_israeli_coefficients_values.py` (extraction-specific)
  - Updated engine tests to verify stage defaulting behavior
  - All 39 tests passing
- **Documentation:**
  - Updated `ai_docs/specs/coefficients_sources.md`: Clear MVP decision statement
  - Updated `data/coefficients/README.md`: Simple FAO-only format
  - Updated `01_STATUS.md`: Phase 3 complete
- **Quality gates:** All passing (ruff check, pytest -q)

### Phase 4: Geospatial Nearest-Point Selection
- **Implementation (app/data/station_matching.py):**
  - Implemented `haversine_km(lat1, lon1, lat2, lon2)` for distance calculation
  - Coordinate validation: raises ValueError for lat outside [-90, 90] or lon outside [-180, 180]
  - Implemented `pick_nearest_point(user_lat, user_lon, points)` for deterministic selection:
    - Computes distance to each point using Haversine formula
    - Selects point with minimum distance
    - Tie-breaker: if equal distances, sorts deterministically by (geographic_area, name, lat, lon) tuple
    - Skips points with invalid coordinates (logs issue, continues with valid points)
    - Raises ValueError if points list is empty or all points have invalid coordinates
  - Implemented `get_nearest_points(user_lat, user_lon, points, k=3)` helper:
    - Returns k nearest points with distances, sorted by distance (nearest first)
    - Useful for debugging and agent UI ("I picked X, alternatives Y/Z")
    - Returns fewer than k if not enough points available
  - Maintained backwards compatibility: legacy aliases `find_nearest_point()` and `calculate_distance()`
- **Script integration (scripts/fetch_forecast.py):**
  - Added `--lat` and `--lon` optional arguments
  - When provided: selects nearest point and prints:
    - Chosen point details (name, area, location, distance_km, evap_mm, date, temp)
    - Top 3 nearest points with distances
  - When not provided: keeps current behavior (shows sample points)
- **Testing (tests/test_geo_selection.py):**
  - `test_haversine_zero_distance()`: distance to self is zero
  - `test_haversine_known_distance()`: Tel Aviv to Jerusalem ~60km verification
  - `test_haversine_invalid_latitude()`: validation for lat outside [-90, 90]
  - `test_haversine_invalid_longitude()`: validation for lon outside [-180, 180]
  - `test_pick_nearest_point_basic()`: basic selection logic
  - `test_pick_nearest_point_empty_list_raises()`: error handling for empty list
  - `test_pick_nearest_point_invalid_coords_raises()`: error when all points invalid
  - `test_pick_nearest_point_skips_invalid_coords()`: skips invalid, uses valid points
  - `test_tie_breaker_is_deterministic()`: tie-breaker produces consistent results
  - `test_get_nearest_points_basic()`: k-nearest returns sorted list with distances
  - `test_get_nearest_points_k_larger_than_available()`: handles k > available points
  - `test_get_nearest_points_empty_list_raises()`: error handling for empty list
  - All tests are offline, deterministic, no network required
- **Selection logic design:**
  - Deterministic: same inputs always produce same output
  - Robust: handles invalid coordinates gracefully (skips, continues with valid)
  - Tie-breaker: uses lexicographic sort on (geographic_area, name, lat, lon) for consistency
  - Distance calculation: Haversine formula (great-circle distance) with Earth radius 6371.0 km
- **Documentation:**
  - Updated `01_STATUS.md`: Phase 4 marked complete, added implementation details
  - Updated `PROJECT_JOURNAL.md`: comprehensive entry documenting selection logic
- **Quality gates:** All passing (ruff check, pytest -q)

### Phase 4.1: Geospatial Selection Improvements (Float Tolerance & Diagnostics)
- **Near-tie handling with epsilon tolerance:**
  - Introduced `EPSILON_KM = 0.001` (1 meter) for floating-point distance comparisons
  - Points within epsilon are considered tied and use deterministic tie-breaker
  - Prevents floating-point precision issues from affecting selection
  - Changed from exact equality (`dist == min_distance`) to tolerance check (`abs(dist - min_distance) <= EPSILON_KM`)
- **Invalid coordinates behavior (two categories):**
  - **User input (--lat/--lon):** Strict validation via `_validate_user_coordinates()`
    - Raises `ValueError` immediately for out-of-range values
    - Clear error messages indicating which coordinate is invalid
  - **Source ForecastPoint coords:** Graceful handling via `_is_valid_coordinate()`
    - Skips invalid points silently (no exception during iteration)
    - Tracks skipped points with diagnostics (name, area, lat, lon)
    - Continues processing with valid points
- **Explicit behavior when no valid points exist:**
  - Created `InvalidCoordinatesError` exception (extends `ValueError`) with rich diagnostics:
    - `total_points`: Total number of points provided
    - `skipped_count`: Number of points skipped
    - `skipped_points`: List of (name, area, lat, lon) tuples for debugging
  - Both `pick_nearest_point()` and `get_nearest_points()` raise `InvalidCoordinatesError` when all points invalid
  - Added `get_selection_diagnostics()` helper function for proactive diagnostics
- **Testing:**
  - `test_pick_nearest_point_near_tie_uses_epsilon()`: Verifies epsilon tolerance triggers tie-breaker
  - `test_pick_nearest_point_near_tie_epsilon_boundary()`: Verifies points outside epsilon are NOT tied
  - `test_pick_nearest_point_invalid_coords_raises()`: Updated to verify `InvalidCoordinatesError` diagnostics
  - `test_get_nearest_points_invalid_coords_raises()`: Tests diagnostics in get_nearest_points
  - `test_pick_nearest_point_user_invalid_coords_raises()`: Tests strict validation for user input
  - `test_get_selection_diagnostics()`: Tests diagnostics helper function
- **Documentation:**
  - Updated `01_STATUS.md`: Added tolerance policy and invalid coordinates behavior
  - Updated `PROJECT_JOURNAL.md`: Documented epsilon tolerance, two-category validation, and diagnostics
- **Quality gates:** All passing (ruff check, pytest -q)

### Phase 4 Complete Summary
- **Geospatial nearest-point selection fully implemented:**
  - Haversine distance calculation with coordinate validation
  - Deterministic nearest point selection with epsilon tolerance for near-ties
  - Two-category invalid coordinates handling (strict for user input, graceful for source data)
  - Rich diagnostics via `InvalidCoordinatesError` exception
  - Script integration with --lat/--lon arguments
  - Comprehensive offline tests (56 tests passing)
- **Status:** Phase 4 complete. Ready for Phase 5 (Strands Agent MVP).

---

## 2025-12-26

### Phase 5: Strands Agent MVP Implementation (Fixed)

- **Dependencies (corrected for real Strands SDK):**
  - `strands-agents>=1.0.0` (imports as `strands`)
  - `strands-agents-tools>=0.1.0` (imports as `strands_tools`)
  - `openai>=1.0.0` (OpenAI API client)
  - `python-dotenv>=1.0.0` for local .env loading
  - Updated pytest markers: Added `llm` marker, default skip with `-m "not network and not llm"`

- **Correct Imports (verified working):**
  ```python
  from strands import Agent, tool
  from strands.models.openai import OpenAIModel
  from strands_tools import calculator, current_time
  ```

- **Security & Configuration:**
  - Created `.env.example` template with OPENAI_API_KEY, IRRIGATION_AGENT_MODEL, ENABLE_VISION
  - Added `.env` to `.gitignore` (never commit secrets)
  - Extended `app/utils/config.py`: Added `irrigation_agent_model` (default: gpt-4o-mini) and `enable_vision`
  - Environment variable parsing for boolean flags (supports 1/0, true/false, yes/no, on/off)

- **Agent Modules:**
  - **app/agents/prompts.py**: System prompt enforcing:
    - Always use tools for calculations (never guess evap/Kc/water amounts)
    - Ask for missing required fields (lat/lon if city/address provided)
    - Keep answers concise (2-6 lines)
    - Include safety note: "Verify with agronomist. Consider soil type, drainage..."
  - **app/agents/schemas.py**: Structured output models:
    - `IrrigationAgentResult`: answer_text, plan, chosen_point, inputs_used, warnings, debug
    - `ChosenPointInfo`: Selected forecast point metadata
  - **app/agents/tools.py**: Strands @tool wrappers (return dicts, not Pydantic for tool compatibility):
    - `tool_get_forecast_points(date_str)`: Fetches forecast data, returns list of dicts
    - `tool_pick_nearest_point(user_lat, user_lon, points)`: Returns {forecast_point, distance_km}
    - `tool_compute_irrigation(profile, forecast_point)`: Returns IrrigationPlan dict
    - Error handling returns `{"error": "message"}` for graceful LLM consumption
  - **app/agents/agent.py**: Agent builder:
    - `build_agent()`: Creates Strands Agent with OpenAIModel
    - Uses OpenAIModel with temperature=0.2 for deterministic outputs
    - Registers built-in tools: current_time, calculator
    - Registers custom irrigation tools
    - Validates OPENAI_API_KEY presence (raises ValueError if missing)

- **CLI Runner:**
  - **scripts/run_agent.py**: Interactive agent CLI:
    - Loads .env file using python-dotenv (only in entrypoint)
    - Validates OPENAI_API_KEY (fails fast with friendly message, never prints key)
    - Builds agent and runs interactive loop
    - Uses `agent(prompt)` call pattern
    - Extracts response from result.message.content
    - Handles KeyboardInterrupt gracefully

- **Testing:**
  - **tests/test_agent_tools.py**: Offline tool tests (13 tests):
    - Uses `pytest.importorskip("strands")` for graceful skip if SDK not available
    - Tests tool_pick_nearest_point with valid/invalid inputs
    - Tests tool_compute_irrigation for farm and plant modes
    - Tests error handling (returns error dict, not exceptions)
  - **tests/test_agent_factory.py**: Agent factory structure tests:
    - `test_agent_build_requires_api_key`: Validates API key requirement
    - `test_agent_module_structure`: Validates module has build_agent
    - `test_tools_module_structure`: Validates tools module has expected functions
  - **tests/test_agent_llm.py**: LLM integration tests (marked @pytest.mark.llm):
    - `test_agent_builds_with_key`: Actual agent creation
    - `test_agent_runs_minimal_prompt`: End-to-end test

- **Quality Gates:**
  - `uv run ruff check .` passes
  - `uv run pytest -q` passes (69 passed, 2 pre-existing failures unrelated to agent)
  - LLM tests gated (skip by default, require OPENAI_API_KEY)

- **Status:** Phase 5 complete. Strands agent MVP working with correct SDK imports.

---

## 2025-12-27

### Phase 6: Google Gemini Migration

- **Decision**: Switched from OpenAI to Google Gemini 2.5 Flash as the primary LLM provider.
- **Rationale**:
  - Gemini 2.5 Flash offers high speed and cost-efficiency.
  - Native Strands provider support for Gemini.
  - Strong tool-calling and structured output capabilities.

- **Dependency Changes**:
  - Updated `pyproject.toml` to replace `strands-agents` and `openai` with `strands-agents[gemini]`.
  - Kept `strands-agents-tools` and `python-dotenv`.
  - Successfully ran `uv sync` to update the environment.

- **Environment & Config**:
  - Updated `.env.example` to use `GOOGLE_API_KEY` and `gemini-2.5-flash`.
  - Updated `app/utils/config.py` to support `irrigation_agent_provider` (defaulting to "gemini") and `IRRIGATION_AGENT_MODEL` (defaulting to `gemini-2.5-flash`).
  - Added `RUN_LLM_TESTS` to config for explicit opt-in.

- **Core Implementation Changes (app/agents/agent.py)**:
  - Replaced `OpenAIModel` with `GeminiModel`.
  - Configured `GeminiModel` with:
    - `temperature: 0.2`
    - `max_output_tokens: 1024`
    - `top_p: 0.9`
  - Kept same tools list (forecast, nearest point, compute irrigation).

- **Performance & Stability Optimizations**:
  - **Data Reduction**: Refactored `tool_get_forecast_points` to return a summary instead of 200+ points.
  - **In-Code Distance Calculation**: Refactored `tool_pick_nearest_point` to calculate the nearest point in Python, sending only the relevant point to the LLM.
  - **Strict Schemas**: Converted all nested dicts in `IrrigationPlan` to Pydantic models to fix Gemini's `additionalProperties` error.
  - **CLI Robustness**: Added `EOFError` handling to `scripts/run_agent.py` to prevent infinite loops on empty input.

- **CLI Runner Updates (scripts/run_agent.py)**:
  - Switched to loading `GOOGLE_API_KEY`.
  - Updated to use `Agent.structured_output(IrrigationAgentResult, prompt)` for stable Gemini output.
  - Output now displays both the human-readable `answer_text` and the full structured JSON.

- **Test Hardening (tests/conftest.py & tests/test_agent_llm.py)**:
  - Updated LLM test gates to require `GOOGLE_API_KEY`.
  - Updated rate limit handling to include Gemini-specific throttling messages.
  - Added `test_agent_structured_output` to verify end-to-end Gemini structured result.

- **Documentation**:
  - Fully updated `ai_docs/specs/agents.md` with Gemini setup and usage instructions.
  - Updated `ai_docs/01_STATUS.md` and `ai_docs/PROJECT_JOURNAL.md`.

- **Verification**:
  - `uv sync` completed successfully.
  - `uv run ruff check .` passes.
  - `uv run pytest -q` passes (offline tests).
  - Manual run with `gemini-2.5-flash` confirmed working end-to-end.

