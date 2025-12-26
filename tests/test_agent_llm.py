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
                pytest.skip("OpenAI rate limit (429) hit - skipping to avoid token waste")
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

    # Extract response text
    if hasattr(result, "message") and result.message:
        content = result.message.get("content", [])
        if content and isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            response_text = "\n".join(text_parts)
        else:
            response_text = str(content)
    else:
        response_text = str(result)

    # The agent should return some text
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
    if hasattr(result, "message") and result.message:
        content = result.message.get("content", [])
        if content and isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            response_text = "\n".join(text_parts)
        else:
            response_text = str(content)
    else:
        response_text = str(result)

    # Should contain the answer (105)
    assert "105" in response_text
