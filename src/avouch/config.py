"""Central configuration for Avouch.

This module is the single source of truth for all settings and secrets.
Every other module imports configuration from here rather than reading
environment variables directly.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and the .env file.

    Pydantic reads each field from the environment (or .env). If a field has
    no default and is not found, Pydantic raises a validation error at startup
    with a clear message naming the missing variable.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    groq_api_key: str = Field(..., description="API key for the Groq provider.")
    gemini_api_key: str = Field(
        ..., description="API key for the Google Gemini provider."
    )
    openrouter_api_key: str = Field(
        ..., description="API key for the OpenRouter provider."
    )
    cerebras_api_key: str = Field(..., description="API key for the Cerebras provider.")

    log_level: str = Field(
        default="INFO",
        description="Logging verbosity: DEBUG, INFO, WARNING, ERROR.",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the application settings, loaded once and cached.

    The lru_cache decorator ensures the .env file is read and validated a
    single time per process; every later call returns the same cached object.
    """
    return Settings()
