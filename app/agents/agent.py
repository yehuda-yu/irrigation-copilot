"""
Strands agent orchestration.

Builds and configures the Strands agent with tools for irrigation planning.
"""

import os
from typing import Any

from strands import Agent
from strands.models.gemini import GeminiModel
from strands_tools import calculator, current_time

from app.agents import prompts
from app.agents.tools import (
    tool_compute_irrigation,
    tool_get_forecast_points,
    tool_pick_nearest_point,
)
from app.utils.config import settings


def build_agent() -> Agent:
    """
    Build and return a configured Strands agent.

    Returns:
        Configured agent instance with irrigation planning tools.

    Raises:
        ValueError: If GOOGLE_API_KEY is not set
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is required. "
            "Create a .env file with GOOGLE_API_KEY=your_key"
        )

    # Get model from env or config (defaults to gemini-2.5-flash)
    model_id = os.environ.get("IRRIGATION_AGENT_MODEL", settings.irrigation_agent_model)

    # Create Gemini model
    model = GeminiModel(
        client_args={"api_key": api_key},
        model_id=model_id,
        params={
            "temperature": 0.2,
            "max_output_tokens": 1024,
            "top_p": 0.9,
        },
    )

    # Build tools list - our custom irrigation tools
    agent_tools: list[Any] = [
        # Built-in tools
        current_time,
        calculator,
        # Custom irrigation tools (wrap our deterministic pipeline)
        tool_get_forecast_points,
        tool_pick_nearest_point,
        tool_compute_irrigation,
    ]

    # Vision is not supported in current version - handled in prompt
    enable_vision = os.environ.get("ENABLE_VISION", "0").lower() in ("1", "true", "yes", "on")
    if enable_vision or settings.enable_vision:
        # Vision tools would be added here when available
        pass

    # Create agent
    agent = Agent(
        model=model,
        system_prompt=prompts.SYSTEM_PROMPT,
        tools=agent_tools,
    )

    return agent
