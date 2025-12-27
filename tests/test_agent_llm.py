"""
LLM integration tests for agent.

CRITICAL: These tests are NEVER run by default, even if OPENAI_API_KEY exists.
They require explicit opt-in via: RUN_LLM_TESTS=1 uv run pytest -m llm

Token-safety measures:
- Minimal prompts (tiny input)
- Low max_tokens where possible
- Single request per test (no loops)
- Graceful skip on rate limit (429)
- Timeout protection
"""


import pytest

# Skip entire module if strands is not available
strands = pytest.importorskip("strands")


def _handle_rate_limit(func):
    """Decorator to skip test on rate limit instead of failing."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            # Check for rate limit indicators
            if "429" in error_str or "rate limit" in error_str or "throttle" in error_str:
                pytest.skip("Google Gemini rate limit hit - skipping to avoid token waste")
            raise

    return wrapper


@pytest.mark.llm
def test_agent_builds_with_key():
    """
    Test that agent builds successfully with API key.

    Cost: Zero tokens (no LLM call, just initialization).
    """
    from app.agents.agent import build_agent

    # conftest.py handles the RUN_LLM_TESTS and API key checks
    agent = build_agent()
    assert agent is not None


@pytest.mark.llm
@_handle_rate_limit
def test_agent_runs_minimal_prompt():
    """
    Test agent runs with minimal prompt and returns valid response.

    Cost: Minimal (~500-1000 tokens total with system prompt + response).
    - Tiny prompt (single sentence)
    - Agent should respond quickly
    """
    from app.agents.agent import build_agent

    agent = build_agent()

    # MINIMAL prompt - single short sentence to minimize tokens
    prompt = "What is 2+2?"

    # Run agent (single call, no retries)
    result = agent(prompt)

    # Check result exists
    assert result is not None

    # Extract response text using a more robust helper or method if available
    # In Strands, result.message['content'] for Gemini might be a list of parts
    response_text = ""
    if hasattr(result, "message") and result.message:
        content = result.message.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    # Check for Strands/OpenAI style or Gemini style
                    if block.get("type") == "text":
                        response_text += block.get("text", "")
                    elif "text" in block:
                        response_text += block["text"]
                elif isinstance(block, str):
                    response_text += block
        else:
            response_text = str(content)
    else:
        response_text = str(result)

    # The agent should return some text
    # If empty, maybe the agent only returned tool calls?
    assert len(response_text) > 0


@pytest.mark.llm
@_handle_rate_limit
def test_agent_uses_calculator_tool():
    """
    Test that agent can use the calculator tool.

    Cost: Minimal (~500-1000 tokens).
    Tests tool calling without irrigation-specific logic.
    """
    from app.agents.agent import build_agent

    agent = build_agent()

    # Prompt that should trigger calculator tool
    prompt = "Calculate: 15 * 7"

    result = agent(prompt)
    assert result is not None

    # Extract response
    response_text = ""
    if hasattr(result, "message") and result.message:
        content = result.message.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        response_text += block.get("text", "")
                    elif "text" in block:
                        response_text += block["text"]
                elif isinstance(block, str):
                    response_text += block
        else:
            response_text = str(content)
    else:
        response_text = str(result)

    # Should contain the answer (105)
    assert "105" in response_text


@pytest.mark.llm
@_handle_rate_limit
def test_agent_structured_output():
    """
    Test that agent can return structured output using Gemini.

    Cost: Minimal (~500-1000 tokens).
    """
    from app.agents.agent import build_agent
    from app.agents.schemas import IrrigationAgentResult

    agent = build_agent()

    # Prompt that includes all necessary info for a simple run
    prompt = (
        "lat=32.0 lon=34.8 Mode=plant plant_profile=herbs pot_diameter_cm=20 "
        "Compute today's irrigation. Use tools."
    )

    result = agent.structured_output(IrrigationAgentResult, prompt)
    assert isinstance(result, IrrigationAgentResult)
    assert result.answer_text
    assert result.plan is not None
    assert result.chosen_point is not None
