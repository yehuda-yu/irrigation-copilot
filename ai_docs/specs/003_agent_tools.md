# Agent Tools Specification

## Tool Functions (app/agents/tools.py)

1. **collect_profile** → ProfileInput
   - Gathers user input: location, area/pot size, crop/plant type, irrigation method

2. **fetch_forecast** → List[ForecastPoint]
   - Calls data adapter, returns normalized forecast points

3. **pick_point** → ForecastPoint
   - Selects appropriate forecast point for user location

4. **lookup_kc** → float
   - Retrieves Kc value from catalog based on crop/plant type

5. **compute** → IrrigationPlan
   - Calls domain engine with profile + forecast + Kc

6. **format_output** → str
   - Formats IrrigationPlan into user-friendly text

## Requirements
- All tools return Pydantic models (structured outputs)
- Tools are deterministic where possible
- Agent orchestrates tool calls via Strands

