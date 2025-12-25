"""
Cache tests.

Offline, deterministic tests for SQLite cache functionality.
"""

import tempfile
from pathlib import Path

from app.storage.cache import ForecastCache


def test_cache_set_and_get_forecast():
    """Test setting and getting forecast from cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "test_cache.sqlite"
        cache = ForecastCache(db_path=cache_path)

        # Test data
        date = "2024-01-15"
        payload = {
            "tempEvapRecord": {
                "areas": {
                    "North": [
                        {
                            "name": "Station A",
                            "lat": 32.5,
                            "long": 34.8,
                            "data": {
                                "2024-01-15": {
                                    "evap": 5.2,
                                    "temp_min": 10.0,
                                    "temp_max": 20.0,
                                },
                            },
                        },
                    ],
                },
            }
        }

        # Set forecast
        cache.set_forecast(date, payload)

        # Get forecast
        retrieved = cache.get_forecast(date)

        assert retrieved is not None
        assert retrieved == payload


def test_cache_miss_returns_none():
    """Test cache miss returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "test_cache.sqlite"
        cache = ForecastCache(db_path=cache_path)

        # Try to get non-existent date
        result = cache.get_forecast("2024-01-15")
        assert result is None


def test_cache_overwrites_existing_entry():
    """Test cache overwrites existing entry for same date."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "test_cache.sqlite"
        cache = ForecastCache(db_path=cache_path)

        date = "2024-01-15"
        payload1 = {"data": "first"}
        payload2 = {"data": "second"}

        # Set first payload
        cache.set_forecast(date, payload1)
        assert cache.get_forecast(date) == payload1

        # Overwrite with second payload
        cache.set_forecast(date, payload2)
        assert cache.get_forecast(date) == payload2


def test_cache_creates_directory_if_missing():
    """Test cache creates directory structure if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "nested" / "dir" / "cache.sqlite"
        # Directory doesn't exist yet
        assert not cache_path.parent.exists()

        cache = ForecastCache(db_path=cache_path)
        # Directory should be created
        assert cache_path.parent.exists()

        # Cache should work
        payload = {"test": "data"}
        cache.set_forecast("2024-01-15", payload)
        assert cache.get_forecast("2024-01-15") == payload


def test_cache_handles_complex_payload():
    """Test cache handles complex nested payload structures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "test_cache.sqlite"
        cache = ForecastCache(db_path=cache_path)

        date = "2024-01-15"
        complex_payload = {
            "tempEvapRecord": {
                "areas": {
                    "North": [
                        {
                            "name": "Station A",
                            "lat": 32.5,
                            "long": 34.8,
                            "data": {
                                "2024-01-15": {
                                    "evap": 5.2,
                                    "temp_min": 10.0,
                                    "temp_max": 20.0,
                                },
                            },
                        },
                    ],
                },
            },
            "metadata": {
                "source": "MoAG",
                "version": "1.0",
            },
        }

        cache.set_forecast(date, complex_payload)
        retrieved = cache.get_forecast(date)

        assert retrieved == complex_payload
        # Verify deep equality
        assert retrieved["tempEvapRecord"]["areas"]["North"][0]["name"] == "Station A"

