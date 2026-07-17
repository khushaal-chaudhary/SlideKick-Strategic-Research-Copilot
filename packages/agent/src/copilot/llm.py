"""
LLM Factory - Creates the right LLM based on configuration.

Supports:
- Groq - Fast inference, generous free tier
- Gemini (Google) - Requires API key
- Ollama (Local) - Free, no limits, great for development
- OpenAI - Requires API key

The per-request provider travels through the agent state (see
ResearchState.llm_provider) rather than module globals, so concurrent
requests with different providers can't race each other.
"""

import logging

from langchain_core.language_models.chat_models import BaseChatModel

from copilot.config.settings import settings

logger = logging.getLogger(__name__)

# Default model per explicitly-requested provider
_PROVIDER_MODELS = {
    "groq": "llama-3.3-70b-versatile",
}


def get_llm(
    temperature: float | None = None,
    provider: str | None = None,
) -> BaseChatModel:
    """
    Get an LLM instance.

    Args:
        temperature: Sampling temperature (defaults to settings.llm_temperature)
        provider: Per-request provider ("ollama", "groq", ...). Falls back to
            settings.llm_provider when omitted.
    """
    temp = temperature if temperature is not None else settings.llm_temperature

    if provider:
        if provider == "ollama":
            model = settings.llm_fallback_model  # Configured local Ollama model
        else:
            model = _PROVIDER_MODELS.get(provider, settings.llm_model)
        logger.debug("Using requested LLM: provider=%s, model=%s", provider, model)
    else:
        provider = settings.llm_provider
        model = settings.llm_model

    logger.debug("Creating LLM: provider=%s, model=%s, temp=%s", provider, model, temp)

    if provider == "groq":
        return _get_groq_llm(model, temp)
    elif provider == "gemini":
        return _get_gemini_llm(model, temp)
    elif provider == "ollama":
        return _get_ollama_llm(model, temp)
    elif provider == "openai":
        return _get_openai_llm(model, temp)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def _get_groq_llm(model: str, temperature: float) -> BaseChatModel:
    """Create a Groq LLM (fast inference)."""
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is required when using Groq.")

    from langchain_groq import ChatGroq

    return ChatGroq(
        model=model,
        temperature=temperature,
        api_key=settings.groq_api_key_str,
    )


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
