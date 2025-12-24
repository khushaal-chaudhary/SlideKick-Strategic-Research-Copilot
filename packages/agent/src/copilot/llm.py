"""
LLM Factory - Creates the right LLM based on configuration.

Supports:
- Gemini (Google) - Default, requires API key
- Ollama (Local) - Free, no limits, great for development
- OpenAI - Requires API key
"""

import logging
from langchain_core.language_models.chat_models import BaseChatModel
from copilot.config.settings import settings

logger = logging.getLogger(__name__)


def get_llm(temperature: float | None = None) -> BaseChatModel:
    """
    Get an LLM instance based on configuration.
    """
    temp = temperature if temperature is not None else settings.llm_temperature
    provider = settings.llm_provider
    model = settings.llm_model
    
    logger.debug("Creating LLM: provider=%s, model=%s, temp=%s", provider, model, temp)
    
    if provider == "gemini":
        return _get_gemini_llm(model, temp)
    elif provider == "ollama":
        return _get_ollama_llm(model, temp)
    elif provider == "openai":
        return _get_openai_llm(model, temp)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def _get_gemini_llm(model: str, temperature: float) -> BaseChatModel:
    """Create a Google Gemini LLM."""
    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY is required when using Gemini.")
    
    import google.generativeai as genai
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    genai.configure(api_key=settings.google_api_key_str)
    
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        client=genai,
        convert_system_message_to_human=True,
    )


def _get_ollama_llm(model: str, temperature: float) -> BaseChatModel:
    """Create an Ollama LLM (local)."""
    from langchain_ollama import ChatOllama
    
    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url=settings.ollama_base_url,
    )


def _get_openai_llm(model: str, temperature: float) -> BaseChatModel:
    """Create an OpenAI LLM."""
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when using OpenAI.")
    
    from langchain_openai import ChatOpenAI
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.openai_api_key_str,
    )