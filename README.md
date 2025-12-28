# Irrigation Copilot

AI-native irrigation planning assistant that generates daily irrigation recommendations based on evaporation forecasts, location, crop profiles, and irrigation methods.

## What It Does

- **Deterministic Planning**: Compute irrigation needs (liters/day for farms, ml/day for plants) using FAO-56 crop coefficients and official evaporation data
- **AI Agent**: Natural language interface for irrigation queries using Google Gemini 2.5 Flash
- **Geospatial Matching**: Automatically selects nearest forecast station based on user location
- **Offline Support**: SQLite cache for forecast data with offline mode for CI/testing

## Architecture in 60 Seconds

**Pure Engine + Adapters + Agent**

- **Domain Layer** (`app/domain/`): Deterministic irrigation calculations. No I/O, no network, no LLM calls.
- **Data Adapters** (`app/data/`): Fetch and normalize evaporation forecasts from MoAG (Israeli Ministry of Agriculture). Cache-friendly with retry logic.
- **Agent Orchestration** (`app/agents/`): Strands agent with Gemini that calls tools (forecast → nearest point → compute → format).
- **API Layer** (`app/api/`): FastAPI endpoints for deterministic planning and agent queries.

All calculations go through the deterministic engine. The agent enforces tool usage—it cannot guess numbers.

## Quickstart (3 Commands)

```bash
# 1. Install dependencies
uv sync

# 2. Start API server
uv run uvicorn app.api.main:app --reload

# 3. Test deterministic endpoint (in another terminal)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/irrigation/plan" -Method POST -ContentType "application/json" -Body '{"lat": 32.0853, "lon": 34.7818, "mode": "farm", "crop_name": "tomato", "area_dunam": 5.0, "stage": "mid"}'
```

See [Demo Scenarios](ai_docs/specs/demo_scenarios.md) for more examples.

## Demo Scenarios

See [`ai_docs/specs/demo_scenarios.md`](ai_docs/specs/demo_scenarios.md) for:
- Farm mode example (tomato, 5 dunam)
- Plant mode example (herbs, 20cm pot)
- Error handling examples (offline cache miss, unknown crop)

## API Endpoints

### Deterministic Planning
**POST** `/irrigation/plan` - Generate irrigation plan without LLM (fast, deterministic)

### AI Agent
**POST** `/agent/run` - Natural language irrigation queries (requires `GOOGLE_API_KEY`)

Full API documentation: [`ai_docs/specs/004_api.md`](ai_docs/specs/004_api.md)

Interactive docs: `http://127.0.0.1:8000/docs` (when server is running)

## Cost & Safety

**Token-Safe Testing:**
- LLM tests are **opt-in only** (`RUN_LLM_TESTS=1` required)
- Even if `GOOGLE_API_KEY` is set, LLM tests skip by default
- Rate limiting on `/agent/run` endpoint (default: 10 req/min)
- Message size limits enforced via Pydantic validation

**Gemini Quota:**
- Uses `gemini-2.5-flash` (cost-effective, fast)
- Monitor usage at [Google AI Studio](https://aistudio.google.com/)

## Limitations / Assumptions

- **ET0 Semantics**: Uses MoAG evaporation data as ET0 (Penman-Monteith) proxy. Exact method not verified with MoAG.
- **Advisory Tool**: Recommendations are advisory only. Not a substitute for agronomic expertise.
- **No Multi-Turn Chat**: Agent is single-turn only (no conversation history).
- **No Vision/VLM**: Image analysis not implemented (deferred to future phase).
- **FAO-56 Coefficients**: Uses FAO-56 stage-based Kc values. Israeli calendar-based coefficients deferred.

## Project Structure

- `app/domain/` - Pure irrigation engine (deterministic math)
- `app/data/` - Forecast adapters (MoAG client, parser, cache)
- `app/agents/` - Strands agent with Gemini (tools, prompts, schemas)
- `app/api/` - FastAPI endpoints (irrigation plan, agent run)
- `app/storage/` - SQLite cache for forecast data
- `data/coefficients/` - FAO-56 crop coefficient files (JSON)
- `tests/` - Test suite (offline by default, LLM tests opt-in)

## Documentation

- [`ai_docs/00_ARCHITECTURE.md`](ai_docs/00_ARCHITECTURE.md) - Architecture overview
- [`ai_docs/01_STATUS.md`](ai_docs/01_STATUS.md) - Current status and phase
- [`ai_docs/specs/`](ai_docs/specs/) - Feature specifications

## Development

```bash
# Run tests (offline, token-safe by default)
uv run pytest -q

# Run LLM tests (requires RUN_LLM_TESTS=1 and GOOGLE_API_KEY)
$env:RUN_LLM_TESTS="1"; uv run pytest -m llm -v

# Lint
uv run ruff check .

# Run agent CLI
uv run python scripts/run_agent.py
```

## License

TBD
