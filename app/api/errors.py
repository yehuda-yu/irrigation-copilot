"""
API error handling and mapping.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Consistent error response format."""

    error: ErrorDetail


def create_error_response(
    status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Helper to create a consistent HTTPException."""
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        },
    )


def map_domain_error_to_http(error: Exception) -> HTTPException:
    """
    Map domain-specific exceptions to FastAPI HTTPExceptions.
    """
    from app.data.forecast_service import OfflineModeError
    from app.data.moag_client import MoAGClientError
    from app.domain.kc_catalog import UnknownCropError

    # Logic for mapping
    if isinstance(error, UnknownCropError):
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="UNKNOWN_CROP",
            message=str(error),
        )

    if isinstance(error, ValueError):
        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=str(error),
        )

    if isinstance(error, OfflineModeError):
        return create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="OFFLINE_CACHE_MISS",
            message=str(error),
        )

    if isinstance(error, MoAGClientError):
        return create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="UPSTREAM_SERVICE_ERROR",
            message=f"Upstream weather service error: {str(error)}",
        )

    # Agent / LLM specific errors (if any, e.g. from strands or gemini)
    error_str = str(error).lower()
    if "rate limit" in error_str or "quota" in error_str:
        return create_error_response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
            message="Upstream AI service rate limit exceeded.",
        )

    # Default fallback
    logger.exception("Unexpected error occurred")
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
    )

