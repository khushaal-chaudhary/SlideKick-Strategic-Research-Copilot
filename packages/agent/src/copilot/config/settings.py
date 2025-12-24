"""
Configuration management using Pydantic Settings.

Supports multiple LLM providers:
- gemini: Google Gemini API (default)
- ollama: Local Ollama server (free, no limits)
- openai: OpenAI API
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Neo4j
    # -------------------------------------------------------------------------
    neo4j_uri: str = Field(..., description="Neo4j connection URI")
    neo4j_username: str = Field(default="neo4j")
    neo4j_password: SecretStr = Field(...)

    # -------------------------------------------------------------------------
    # LLM Provider Selection
    # -------------------------------------------------------------------------
    llm_provider: Literal["gemini", "ollama", "openai"] = Field(
        default="gemini",
        description="Which LLM provider to use: gemini, ollama, or openai",
    )
    llm_model: str = Field(
        default="gemini-1.5-flash",
        description="Model name (e.g., gemini-1.5-flash, llama3.1:8b, gpt-4o-mini)",
    )
    llm_temperature: float = Field(default=0.0)

    # -------------------------------------------------------------------------
    # Google Gemini (if llm_provider=gemini)
    # -------------------------------------------------------------------------
    google_api_key: SecretStr | None = Field(default=None)

    # -------------------------------------------------------------------------
    # Ollama (if llm_provider=ollama)
    # -------------------------------------------------------------------------
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )

    # -------------------------------------------------------------------------
    # OpenAI (if llm_provider=openai)
    # -------------------------------------------------------------------------
    openai_api_key: SecretStr | None = Field(default=None)

    # -------------------------------------------------------------------------
    # Tavily (Web Search)
    # -------------------------------------------------------------------------
    tavily_api_key: SecretStr | None = Field(
        default=None,
        description="Tavily API key for AI-powered web search",
    )

    # -------------------------------------------------------------------------
    # Alpha Vantage (Financial Data)
    # -------------------------------------------------------------------------
    alpha_vantage_api_key: SecretStr | None = Field(
        default=None,
        description="Alpha Vantage API key for financial data (free at alphavantage.co)",
    )

    # -------------------------------------------------------------------------
    # LangSmith
    # -------------------------------------------------------------------------
    langchain_tracing_v2: bool = Field(default=True)
    langchain_api_key: SecretStr | None = Field(default=None)
    langchain_project: str = Field(default="strategic-research-copilot")

    # -------------------------------------------------------------------------
    # Google Slides MCP
    # -------------------------------------------------------------------------
    google_client_id: str | None = Field(default=None)
    google_client_secret: SecretStr | None = Field(default=None)
    google_refresh_token: SecretStr | None = Field(default=None)

    # -------------------------------------------------------------------------
    # Agent Configuration
    # -------------------------------------------------------------------------
    quality_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum quality score to proceed without retry",
    )
    max_iterations: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum research loops before giving up",
    )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    @property
    def neo4j_password_str(self) -> str:
        return self.neo4j_password.get_secret_value()

    @property
    def google_api_key_str(self) -> str:
        if self.google_api_key:
            return self.google_api_key.get_secret_value()
        return ""

    @property
    def openai_api_key_str(self) -> str:
        if self.openai_api_key:
            return self.openai_api_key.get_secret_value()
        return ""

    @property
    def tavily_api_key_str(self) -> str:
        if self.tavily_api_key:
            return self.tavily_api_key.get_secret_value()
        return ""

    @property
    def alpha_vantage_api_key_str(self) -> str:
        if self.alpha_vantage_api_key:
            return self.alpha_vantage_api_key.get_secret_value()
        return ""

    @property
    def langsmith_enabled(self) -> bool:
        return self.langchain_tracing_v2 and self.langchain_api_key is not None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()