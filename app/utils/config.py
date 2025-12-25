"""
Application configuration and settings.

Loads settings from environment variables or config files.
Uses Pydantic Settings for validation.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # MoAG API settings
    moag_base_url: str = ""
    moag_timeout_seconds: int = 30
    moag_retries: int = 3
    moag_backoff_base_seconds: float = 1.0

    # Cache settings
    cache_db_path: str = ".cache/forecast.sqlite"
    cache_ttl_days: int = 7

    # Offline mode (set OFFLINE_MODE=1 or True to enable)
    offline_mode: bool = False

    # Logging
    log_level: str = "INFO"

    @field_validator("offline_mode", mode="before")
    @classmethod
    def parse_offline_mode(cls, v: str | bool | int) -> bool:
        """Parse offline_mode from env var (supports 1/0, true/false, etc.)."""
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return bool(v)
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes", "on")
        return False


# Global settings instance
settings = Settings()
