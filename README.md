# Irrigation Copilot

AI-native irrigation planning assistant that generates daily/weekly irrigation recommendations based on evaporation forecasts, location, crop profiles, and irrigation methods.

## Quick Start

### Installation

```bash
pip install -e ".[dev]"
```

### Run API Server

```bash
uvicorn app.api.main:app --reload
```

### Run Agent CLI

```bash
python scripts/run_agent_cli.py
```

### Run Tests

```bash
pytest
```

## Project Structure

- `app/domain/` - Pure engine (deterministic math, no I/O)
- `app/data/` - Data adapters (MoAG, IMS)
- `app/agents/` - Strands agent orchestration
- `app/api/` - FastAPI endpoints
- `app/storage/` - SQLite cache
- `scripts/` - Utility scripts
- `tests/` - Test suite
- `ai_docs/` - Architecture and specifications

## Documentation

**Start here:** Read `ai_docs/00_ARCHITECTURE.md` for architecture overview and `ai_docs/01_STATUS.md` for current status.

- `ai_docs/00_ARCHITECTURE.md` - Architecture and design principles
- `ai_docs/01_STATUS.md` - Current phase and status
- `ai_docs/PROJECT_JOURNAL.md` - Decision log
- `ai_docs/specs/` - Feature specifications

## Development Rules

See `.cursor/rules/` for development guidelines:
- Always read architecture docs before coding
- Domain layer must stay pure (no I/O)
- All agent tools return Pydantic models
- Small, scoped changes only

## License

TBD

