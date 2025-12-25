"""
MoAG (Ministry of Agriculture) forecast API client.

Fetches daily evaporation and temperature forecasts from MoAG farmers forecast endpoint.
Handles HTTP requests, timeouts, and retries with Chrome-like headers.
"""

import logging
import re
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

# MoAG API endpoint
MOAG_BASE_URL = "https://f0to4m65wf.execute-api.eu-north-1.amazonaws.com/Forecast/farmers_forecast/new-get-temp-evap-data"


class MoAGClientError(RuntimeError):
    """Custom exception for MoAG API errors."""

    def __init__(
        self, message: str, status_code: int | None = None, response_snippet: str | None = None
    ):
        """
        Initialize MoAG client error.

        Args:
            message: Error message
            status_code: HTTP status code if available
            response_snippet: First 300-500 chars of response if available
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_snippet = response_snippet


def validate_date_format(date: str) -> None:
    """
    Validate date format is YYYY-MM-DD.

    Args:
        date: Date string to validate

    Raises:
        ValueError: If date format is invalid
    """
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date):
        raise ValueError(
            f"Invalid date format: '{date}'. Expected YYYY-MM-DD format (e.g., '2024-01-15')"
        )


def fetch_forecast_raw(
    date: str,
    max_retries: int | None = None,
    retry_delay: float | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    """
    Fetch raw forecast data from MoAG API for given date.

    Args:
        date: Forecast date in YYYY-MM-DD format
        max_retries: Maximum number of retry attempts (defaults to settings.moag_retries)
        retry_delay: Delay between retries in seconds
                     (defaults to settings.moag_backoff_base_seconds)
        timeout: Request timeout in seconds (defaults to settings.moag_timeout_seconds)

    Returns:
        Raw API response dictionary

    Raises:
        ValueError: If date format is invalid
        MoAGClientError: On HTTP errors, JSON decode errors, or network failures
    """
    from app.utils.config import settings

    validate_date_format(date)

    # Use config defaults if not provided
    if max_retries is None:
        max_retries = settings.moag_retries
    if retry_delay is None:
        retry_delay = settings.moag_backoff_base_seconds
    if timeout is None:
        timeout = settings.moag_timeout_seconds

    # Chrome-like headers to mimic browser navigation
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }

    url = f"{MOAG_BASE_URL}?date={date}"

    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Fetching forecast from MoAG API (attempt {attempt + 1}/{max_retries}): {url}"
            )
            response = requests.get(url, headers=headers, timeout=timeout)

            # Check HTTP status
            if not response.ok:
                status_code = response.status_code
                response_text = response.text[:500]
                error_msg = (
                    f"MoAG API returned HTTP {status_code} for date {date}. "
                    f"Response snippet: {response_text[:300]}... "
                    f"This may be due to WAF/header mismatch. Check headers or try again later."
                )
                raise MoAGClientError(
                    error_msg, status_code=status_code, response_snippet=response_text
                )

            # Parse JSON
            try:
                payload = response.json()
                logger.info(f"Successfully fetched forecast for date: {date}")
                return payload
            except ValueError as e:
                response_text = response.text[:500]
                error_msg = (
                    f"Failed to parse JSON response from MoAG API for date {date}. "
                    f"Response snippet: {response_text[:300]}... "
                    f"This may be due to WAF/header mismatch or API changes."
                )
                raise MoAGClientError(error_msg, response_snippet=response_text) from e

        except requests.exceptions.Timeout as e:
            last_error = MoAGClientError(
                f"Request timeout after {timeout}s for date {date}. "
                f"MoAG API may be slow or unavailable.",
                response_snippet=str(e),
            )
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}: {e}")

        except requests.exceptions.RequestException as e:
            last_error = MoAGClientError(
                f"Network error fetching forecast for date {date}: {e}",
                response_snippet=str(e)[:300],
            )
            logger.warning(f"Network error on attempt {attempt + 1}/{max_retries}: {e}")

        except MoAGClientError:
            # Re-raise MoAGClientError immediately (no retry for HTTP/JSON errors)
            raise

        # Wait before retry (except on last attempt)
        if attempt < max_retries - 1:
            time.sleep(retry_delay * (attempt + 1))  # Exponential backoff

    # All retries exhausted
    if last_error:
        raise last_error
    raise MoAGClientError(f"Failed to fetch forecast for date {date} after {max_retries} attempts")
