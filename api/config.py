"""
API Configuration and Settings.

Uses Pydantic Settings for environment variable management.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Configuration
    api_title: str = "SlideKick API"
    api_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # CORS Origins
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://khushaalchaudhary.com",
    ]

    # Neo4j Configuration
    neo4j_uri: str = ""
    neo4j_username: str = "neo4j"
    neo4j_password: str = ""

    # LLM Configuration
    google_api_key: str = ""
    groq_api_key: str = ""

    # Web Search (Tavily)
    tavily_api_key: str = ""

    # Alpha Vantage Financial Data
    alpha_vantage_api_key: str = ""

    # Agent Configuration
    max_iterations: int = 3
    quality_threshold: float = 0.7


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
