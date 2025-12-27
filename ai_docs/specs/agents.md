# Agent Specification

## Overview

The Irrigation Copilot uses a **Strands-based conversational agent** that orchestrates
deterministic tools to provide irrigation recommendations. The agent enforces strict tool
usage for all calculations and data retrieval. It uses **Google Gemini 2.5 Flash** as the
underlying LLM.

## Architecture

- **Agent Layer**: `app/agents/agent.py` - Builds Strands agent with Gemini model
- **Tools**: `app/agents/tools.py` - Strands `@tool` wrappers around domain/data functions
- **Prompts**: `app/agents/prompts.py` - System prompt enforcing tool usage
- **Schemas**: `app/agents/schemas.py` - Structured output models (IrrigationAgentResult)

## Setup

### 1. Create .env File

Copy `.env.example` to `.env` and fill in your Google API key (get one from [Google AI Studio](https://aistudio.google.com/)):

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

Example `.env`:

```
GOOGLE_API_KEY=your-key-here
IRRIGATION_AGENT_MODEL=gemini-2.5-flash
ENABLE_VISION=0
OFFLINE_MODE=0
```

**Security**: Never commit `.env` to git. It's already in `.gitignore`.

### 2. Install Dependencies

```bash
uv sync
```

This installs:
- `strands-agents[gemini]` - The Strands agent framework with Gemini support
- `strands-agents-tools` - Built-in tools (calculator, current_time)
- `python-dotenv` - Load .env files

### 3. Run Agent CLI

```bash
uv run python scripts/run_agent.py
```

## Usage

### Interactive CLI

The agent runs in an interactive loop and returns structured results:

```
You: lat=32.0853 lon=34.7818 Mode=plant plant_profile=herbs pot_diameter_cm=20 Compute today's irrigation. Use tools. Return structured JSON.

Agent Answer:
--------------------
Based on today's evaporation of 5.8mm and your herbs' profile, you should irrigate with 450ml today.
--------------------

Structured Result (JSON):
{
  "answer_text": "Based on today's evaporation of 5.8mm and your herbs' profile, you should irrigate with 450ml today.",
  "plan": { ... },
  ...
}
```

### Expected Flow

1. User provides: mode (farm/plant), location (lat/lon), area/pot size, crop/plant name
2. Agent calls `tool_get_forecast_points` to fetch evaporation data
3. Agent calls `tool_pick_nearest_point` to select nearest forecast station
4. Agent calls `tool_compute_irrigation` to calculate water needs
5. Agent returns a structured `IrrigationAgentResult` including a short text answer and a full plan.

## Tools

### Built-in Tools (from strands_tools)

- `current_time` - Get current date/time
- `calculator` - Perform calculations

### Custom Tools (from app/agents/tools.py)

- `tool_get_forecast_points(date_str)` - Fetch forecast data (respects offline mode)
- `tool_pick_nearest_point(user_lat, user_lon, points)` - Select nearest forecast point
- `tool_compute_irrigation(profile, forecast_point)` - Compute irrigation plan

All irrigation calculations go through our deterministic engine. The agent MUST use these
tools - it cannot guess or calculate numbers on its own.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | - | Google Gemini API key |
| `IRRIGATION_AGENT_MODEL` | No | `gemini-2.5-flash` | Model to use |
| `ENABLE_VISION` | No | `0` | Enable image reading tool |
| `OFFLINE_MODE` | No | `0` | Use cache only, no forecast API calls |
| `RUN_LLM_TESTS` | No | `0` | Set to 1 to enable LLM tests |

### Model Selection

**Recommended**: `gemini-2.5-flash` (default)

- Highly cost-effective
- Fast responses
- Strong tool-calling and structured output support
- Large context window

## Cost Optimization

1. **Use gemini-2.5-flash** - Default, sufficient for most queries
2. **Keep answers short** - System prompt enforces 2-6 line answers
3. **Cache forecasts** - Use offline mode after initial fetch to avoid API calls
4. **Temperature 0.2** - Low temperature for consistent, deterministic outputs

## Testing

### Token-Safety Policy

**CRITICAL**: LLM tests are NEVER run by default, even if GOOGLE_API_KEY is set.
This prevents accidental token burn in local development and CI.

Two gates must be passed:
1. `RUN_LLM_TESTS=1` environment variable (explicit opt-in)
2. `GOOGLE_API_KEY` must be set

Additional safeguards:
- LLM tests skip (not fail) on rate limit or throttling
- LLM tests cannot run with pytest-xdist parallel execution
- Prompts are minimal to reduce token usage

### Offline Tests (Default - no API key needed)

```bash
# Test tool wrappers with synthetic data
uv run pytest tests/test_agent_tools.py -v

# Test agent factory structure
uv run pytest tests/test_agent_factory.py -v

# Run all offline tests (LLM tests are skipped even if API key exists)
uv run pytest -q
```

### LLM Integration Tests (requires explicit opt-in)

LLM tests require BOTH conditions:
1. `RUN_LLM_TESTS=1` - Explicit opt-in flag
2. `GOOGLE_API_KEY` - API key set

```bash
# Windows PowerShell:
$env:RUN_LLM_TESTS="1"; uv run pytest -m llm -v

# Windows CMD:
set RUN_LLM_TESTS=1 && uv run pytest -m llm -v

# Linux/Mac bash:
RUN_LLM_TESTS=1 uv run pytest -m llm -v
```

Without `RUN_LLM_TESTS=1`, tests will skip even if GOOGLE_API_KEY is present:
```
SKIPPED [1] tests/conftest.py: LLM tests require explicit opt-in: set RUN_LLM_TESTS=1
```

### Run All Tests (Token-Safe by Default)

```bash
uv run pytest -q  # LLM and network tests are deselected by default
```

### Network Tests

Network tests (non-LLM HTTP calls) are also skipped by default.
Run explicitly with:

```bash
uv run pytest -m network -v  # No API key needed, just network access
```

## Example Session

```
$ uv run python scripts/run_agent.py
Loaded environment from c:\irrigation-copilot\irrigation-copilot\.env
Model: gemini-2.5-flash
Building agent...
[OK] Agent ready!

============================================================
Irrigation Copilot Agent
============================================================
Type your question (or 'quit'/'exit' to stop)

Example: I have a 5 dunam tomato farm at lat 32.0, lon 34.8.
         What irrigation do I need today?

You: I have a 5 dunam tomato farm at lat 32.0, lon 34.8. What do I need today?

[Thinking...]

Agent Answer:
--------------------
Your 5 dunam tomato farm needs approximately 3,200 liters/day today.
This is based on 5.8mm evaporation from the nearest forecast station (Bet Dagan,
12.5 km away) and mid-stage Kc coefficient of 1.15 for tomatoes.

Recommendation: Consider splitting into 2 irrigation pulses for optimal
water distribution.

Verify with agronomist. Consider soil type, drainage, and irrigation system
efficiency.
--------------------

Structured Result (JSON):
{
  "answer_text": "Your 5 dunam tomato farm needs approximately 3,200 liters/day today...",
  "plan": { ... },
  ...
}
```

## Safety Notes

The agent always includes:
- "Verify with agronomist. Consider soil type, drainage, and irrigation system efficiency."

This is enforced in the system prompt to ensure users consult professionals for critical
decisions.

## Imports Reference

The correct imports for the Strands SDK:

```python
# Agent and tool decorator
from strands import Agent, tool

# Gemini model
from strands.models.gemini import GeminiModel

# Built-in tools
from strands_tools import calculator, current_time
```
