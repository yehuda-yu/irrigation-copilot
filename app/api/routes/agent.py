"""
Agent routes.
"""

import logging
import time
from typing import Dict, List

from fastapi import APIRouter, HTTPException, status

from app.agents.agent import build_agent
from app.agents.schemas import IrrigationAgentResult
from app.api.errors import map_domain_error_to_http
from app.api.schemas.agent import AgentRunRequest, AgentRunResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory rate limiting
# Key: client identifier (ip or just global for now), Value: list of timestamps
_request_history: Dict[str, List[float]] = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 10  # per window

def check_rate_limit(client_id: str = "default"):
    """Very simple in-memory rate limiting."""
    now = time.time()
    if client_id not in _request_history:
        _request_history[client_id] = []

    # Filter for requests in the current window
    _request_history[client_id] = [
        t for t in _request_history[client_id] if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_request_history[client_id]) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    _request_history[client_id].append(now)
    return True


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest):
    """
    Run the AI agent to process a natural language irrigation query.
    """
    # 1. Guardrails: Rate limiting
    if not check_rate_limit():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                }
            }
        )

    # 2. Guardrails: Message size (already handled by Pydantic min_length/max_length in schema)
    # But double checking here if needed.

    try:
        # 3. Build agent
        # Note: In a production app, you might want to reuse the agent instance or
        # use a pool, but build_agent() is what we have.
        agent = build_agent()

        # 4. Execute agent with structured output
        # Use a timeout if possible. Strands/Gemini might have their own timeouts.
        # Here we just run it.
        logger.info(f"Running agent with message: {request.message[:50]}...")

        # We can pass offline mode if the tools support it.
        # Our tools currently read from settings.offline_mode.
        # We might need to monkeypatch settings or pass it down.
        # For now, we assume the environment/settings are configured correctly.
        # If we wanted to support per-request offline mode for the agent,
        # we'd need to modify the tools.

        result = agent.structured_output(IrrigationAgentResult, request.message)

        return AgentRunResponse(result=result)

    except Exception as e:
        logger.error(f"Error in /agent/run: {str(e)}")
        raise map_domain_error_to_http(e)

