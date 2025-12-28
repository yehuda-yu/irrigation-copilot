"""
Agent API schemas.
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.agents.schemas import IrrigationAgentResult


class AgentRunRequest(BaseModel):
    """Request schema for running the AI agent."""

    message: str = Field(
        ..., min_length=1, max_length=5000, description="User message to the agent"
    )
    offline: Optional[bool] = Field(
        None, description="If True, agent tools will only use cached data"
    )


class AgentRunResponse(BaseModel):
    """Response schema for agent execution."""

    result: IrrigationAgentResult

