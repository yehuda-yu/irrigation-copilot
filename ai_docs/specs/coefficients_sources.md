# Irrigation Coefficients Sources

This document describes the coefficient data sources used in the irrigation engine.

## MVP Decision: FAO-56 Stage-Based Kc Only

**Decision**: MVP uses FAO-56 stage-based crop coefficients exclusively. Israel-first approach deferred to future phase.

**Rationale**:
- Simpler, more maintainable for MVP
- FAO-56 is globally recognized and well-documented
- Stage-based approach is sufficient for initial use cases
- Israeli calendar-based coefficients can be added later if needed

## Source: FAO-56

### FAO Irrigation and Drainage Paper No. 56
- **Title**: Crop evapotranspiration - Guidelines for computing crop water requirements
- **Chapter**: Chapter 6 - ETc - Single crop coefficient (Kc)
- **URL**: https://www.fao.org/4/x0490e/x0490e0b.htm
- **Table**: Table 12 (Kc values for various crops)
- **Type**: Kc (crop coefficient)
- **Basis**: ET0 Penman-Monteith reference evapotranspiration
- **Format**: Stage-based (Kc_ini, Kc_mid, Kc_end)

## Data Model

**Simple FAO-only structure**:
- Each crop JSON file contains:
  - `coefficients.type`: "stage"
  - `coefficients.basis`: "ET0 Penman-Monteith"
  - `coefficients.kc_initial`: float
  - `coefficients.kc_mid`: float
  - `coefficients.kc_end`: float
  - `metadata.source`: FAO-56 source information

## Coefficient Files

All coefficient data is stored in `data/coefficients/*.json` files.

See `data/coefficients/README.md` for file format details.

## Forecast "evap" Field Semantics

**Status**: **Confirmed - ET0 Penman-Monteith**

**MoAG Forecast Field**: `evap` (daily evaporation in mm)

**Basis**: ET0 Penman-Monteith reference evapotranspiration

**Usage**: Used directly as ET0 in irrigation calculations (evap_mm * Kc)

**Documentation**: All coefficient files and engine code document ET0 Penman-Monteith basis consistently.

## Future: Israeli Coefficients

Israeli MoA/SHAHAM calendar-based coefficients may be added in a future phase if needed. The current simple structure can be extended without breaking changes.
