"""
Offline tests for agent factory.

Tests agent building logic without requiring API key or network calls.
"""

import os

import pytest

# Skip these tests if strands is not available
pytest.importorskip("strands")


def test_agent_build_requires_api_key():
    """Test that build_agent raises error when GOOGLE_API_KEY is missing."""
    from app.agents.agent import build_agent

    # Temporarily remove API key if present
    original_key = os.environ.pop("GOOGLE_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
            build_agent()
    finally:
        # Restore original key if it existed
        if original_key:
            os.environ["GOOGLE_API_KEY"] = original_key


def test_agent_module_structure():
    """Test that agent module has expected structure."""
    from app.agents import agent

    assert hasattr(agent, "build_agent")


def test_tools_module_structure():
    """Test that tools module has expected functions."""
    from app.agents import tools

    assert hasattr(tools, "tool_get_forecast_points")
    assert hasattr(tools, "tool_pick_nearest_point")
    assert hasattr(tools, "tool_compute_irrigation")


def test_prompts_module_structure():
    """Test that prompts module has expected content."""
    from app.agents import prompts

    assert hasattr(prompts, "SYSTEM_PROMPT")
    assert len(prompts.SYSTEM_PROMPT) > 100  # Should be substantial


def test_schemas_module_structure():
    """Test that schemas module has expected models."""
    from app.agents import schemas

    assert hasattr(schemas, "IrrigationAgentResult")
    assert hasattr(schemas, "ChosenPointInfo")
