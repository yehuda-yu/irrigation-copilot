# Irrigation Copilot: Architecture & Project Status

**Mandatory Reading:** This file is the single source of truth for architecture. Read it before making changes.

## 1) High-Level Goal

Build an AI-native **Irrigation Copilot** that outputs daily/weekly irrigation recommendations based on:
- Official/credible daily evaporation (evap / ET0 proxy)
- User location + area (farm) or pot size (houseplant)
- Crop / plant profile (Kc-like mapping)
- Irrigation method efficiency

Two modes:
1) **Farm mode:** mm/day + liters/dunam + pulse schedule
2) **Home-plant mode:** ml/day + simple schedule + shareable "card text"

## 2) Core Architecture: "Pure Engine" + Adapters + Agent

Strict separation of responsibilities:

- **Domain (Pure Engine):** `app/domain/*`
  - Deterministic math only. No network, no filesystem, no LLM calls.
  - Unit conversions, Kc/plant profiles, irrigation computations.
- **Data Adapters:** `app/data/*`
  - Fetch + parse + normalize evaporation/weather data into `ForecastPoint`.
  - Must be cache-friendly and resilient (timeouts/retries).
- **Agent Orchestration:** `app/agents/*`
  - Strands Agent that calls tools: collect_profile → fetch_forecast → pick_point → lookup_kc → compute → format_output
  - All tool outputs are structured (Pydantic).
- **API Layer (optional early, required later):** `app/api/*`
  - FastAPI endpoints to expose: health, irrigation plan, forecast summary.
- **Storage/Cache:** `app/storage/cache.py`
  - SQLite cache for daily forecast pulls and derived results.

## 3) Key Files

- `app/domain/models.py`: **API + Agent contract models** (ProfileInput, ForecastPoint, IrrigationPlan)
- `app/domain/irrigation_engine.py`: **Core compute** (liters = evap_mm * area_m2 * Kc / efficiency)
- `app/data/moag_client.py` + `app/data/moag_parser.py`: **MoAG forecast adapter** (evap + temps normalized)
- `app/agents/strands_agent.py`: **Agent entrypoint** (build_agent)
- `app/agents/tools.py`: **Tool layer** (functions callable by the agent)
- `ai_docs/01_STATUS.md`: **Current phase + todo**
- `ai_docs/PROJECT_JOURNAL.md`: **Append-only decision log**

## 4) Data Strategy (MVP)

MVP uses the existing MoAG "farmers forecast" endpoint adapter (best-effort).
Optional later: add IMS adapter for official station API.

Normalized data model:
- `ForecastPoint`: date, lat, lon, evap_mm, temp_min, temp_max, name, area

## 5) Agent Strategy (MVP)

Use **Strands** for fast MVP.
Later "CV upgrade": add LangGraph workflow with:
- station/point selection approval (human-in-the-loop)
- durable execution / checkpoints

## 6)  Current Status (High-Level)

**Phase:** Scaffold + MoAG adapter + Pure Engine tests (MVP foundations)

