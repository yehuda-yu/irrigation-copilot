"""
Application configuration and settings.

Loads settings from environment variables or config files.
Uses Pydantic Settings for validation.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # MoAG API settings
    moag_base_url: str = ""
    moag_timeout: int = 30

    # Cache settings
    cache_db_path: str = "irrigation_cache.db"
    cache_ttl_days: int = 7

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

