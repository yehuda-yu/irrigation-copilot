"""
Strands agent orchestration (legacy entrypoint).

This module is kept for backwards compatibility.
Use app.agents.agent.build_agent() instead.
"""

from app.agents.agent import build_agent

__all__ = ["build_agent"]
