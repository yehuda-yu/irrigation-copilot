"""
SQLite cache for forecast data and computed results.

Caches daily forecast pulls to avoid redundant API calls.
Stores raw payloads by date for efficient retrieval.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ForecastCache:
    """
    SQLite cache for forecast data.

    Stores raw forecast payloads by date for efficient retrieval.
    """

    def __init__(self, db_path: Path | str | None = None):
        """
        Initialize cache with SQLite database.

        Args:
            db_path: Path to SQLite database file (defaults to settings.cache_db_path)
        """
        from app.utils.config import settings

        if db_path is None:
            db_path = settings.cache_db_path
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS forecast_cache (
                    date TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    fetched_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def get_forecast(self, date: str) -> Optional[dict]:
        """
        Retrieve cached forecast payload for date.

        Args:
            date: Forecast date in YYYY-MM-DD format

        Returns:
            Cached payload dictionary or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                cursor = conn.execute(
                    "SELECT payload_json FROM forecast_cache WHERE date = ?",
                    (date,),
                )
                row = cursor.fetchone()
                if row:
                    logger.info(f"Cache hit for date: {date}")
                    result = json.loads(row[0])
                    return result
                logger.info(f"Cache miss for date: {date}")
                return None
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error reading cache for date {date}: {e}")
            return None

    def set_forecast(self, date: str, payload: dict) -> None:
        """
        Store forecast payload in cache.

        Args:
            date: Forecast date in YYYY-MM-DD format
            payload: Raw API response dictionary to cache
        """
        try:
            fetched_at = datetime.now().isoformat()
            payload_json = json.dumps(payload)
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO forecast_cache (date, payload_json, fetched_at)
                    VALUES (?, ?, ?)
                    """,
                    (date, payload_json, fetched_at),
                )
                conn.commit()
                logger.info(f"Cached forecast for date: {date}")
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error caching forecast for date {date}: {e}")
            raise
