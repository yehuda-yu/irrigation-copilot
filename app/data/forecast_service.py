"""
Forecast service - main entry point for fetching forecast data.

Orchestrates cache, API client, and parser to provide a stable API
for retrieving forecast points.
"""

import logging
from datetime import datetime
from pathlib import Path

from app.data.moag_client import MoAGClientError, fetch_forecast_raw
from app.data.moag_parser import parse_forecast_points
from app.domain.models import ForecastPoint
from app.storage.cache import ForecastCache
from app.utils.config import settings

logger = logging.getLogger(__name__)

# Default cache instance (can be overridden for testing)
_default_cache: ForecastCache | None = None


def get_cache() -> ForecastCache:
    """Get or create default cache instance."""
    global _default_cache
    if _default_cache is None:
        cache_path = Path(settings.cache_db_path)
        _default_cache = ForecastCache(db_path=cache_path)
    return _default_cache


class OfflineModeError(RuntimeError):
    """Raised when offline mode is enabled but cache is unavailable."""

    pass


def get_forecast_points(
    date_str: str | None = None,
    cache: ForecastCache | None = None,
    offline_mode: bool | None = None,
) -> list[ForecastPoint]:
    """
    Get forecast points for a given date.

    Tries cache first, then fetches from API if needed (unless offline_mode=True).
    Falls back to stale cache if fetch fails but cache exists.

    Args:
        date_str: Forecast date in YYYY-MM-DD format (defaults to today)
        cache: Optional cache instance (uses default if not provided)
        offline_mode: If True, skip network fetch and only use cache.
                     If None, reads from settings.offline_mode

    Returns:
        List of ForecastPoint objects

    Raises:
        ValueError: If date format is invalid
        MoAGClientError: If fetch fails and no cache exists (when offline_mode=False)
        OfflineModeError: If offline_mode=True and cache miss occurs
    """
    if date_str is None:
        date_str = datetime.now().date().isoformat()

    # Determine offline mode (explicit arg > config > default False)
    is_offline = offline_mode if offline_mode is not None else settings.offline_mode

    cache_instance = cache or get_cache()

    # Try cache first
    cached_payload = cache_instance.get_forecast(date_str)
    if cached_payload is not None:
        logger.info(f"Using cached forecast for date: {date_str}")
        return parse_forecast_points(cached_payload)

    # Cache miss
    if is_offline:
        error_msg = (
            f"Offline mode enabled: cache miss for date {date_str}. "
            f"Run once online to populate cache, or disable offline mode."
        )
        logger.error(error_msg)
        raise OfflineModeError(error_msg)

    # Cache miss - fetch from API
    logger.info(f"Cache miss for date {date_str}, fetching from MoAG API")
    try:
        payload = fetch_forecast_raw(date_str)
        # Store in cache
        cache_instance.set_forecast(date_str, payload)
        # Parse and return
        return parse_forecast_points(payload)
    except MoAGClientError as e:
        # Fetch failed - try stale cache as fallback
        logger.warning(f"Fetch failed for date {date_str}: {e}")
        stale_payload = cache_instance.get_forecast(date_str)
        if stale_payload is not None:
            logger.info(f"Using stale cached data for date {date_str} as fallback")
            return parse_forecast_points(stale_payload)
        # No cache available - re-raise the error
        raise

