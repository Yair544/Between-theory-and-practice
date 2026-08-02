"""
Provider selection.

`build_client` returns None in offline mode. Returning None rather than raising
is deliberate: running without a model is a supported mode, not a failure, and
the caller is expected to fall back to the deterministic engine.
"""

from __future__ import annotations

from ...config import Settings
from .base import LLMClient, LLMError, LLMResult, parse_json_object

__all__ = ["LLMClient", "LLMError", "LLMResult", "parse_json_object",
           "build_client", "build_alternate_client"]


def _make(provider: str, settings: Settings) -> LLMClient | None:
    """Construct one provider's client, importing its SDK only if used."""
    if provider == "anthropic" and settings.anthropic_api_key:
        from .anthropic_client import AnthropicClient
        return AnthropicClient(settings.anthropic_api_key, settings.anthropic_model)

    if provider == "gemini" and settings.gemini_api_key:
        from .gemini_client import GeminiClient
        return GeminiClient(settings.gemini_api_key, settings.gemini_model)

    if provider == "openai" and settings.openai_api_key:
        from .openai_client import OpenAIClient
        return OpenAIClient(settings.openai_api_key, settings.openai_model)

    return None


def build_client(settings: Settings) -> LLMClient | None:
    """The client for the configured provider, or None when offline."""
    if settings.offline:
        return None
    return _make(settings.provider, settings)


def build_alternate_client(settings: Settings) -> LLMClient | None:
    """
    A *different* configured provider, if any.

    Used by tools/compare_models.py to run one prompt through two vendors and
    diff the conclusions. Order is arbitrary; the point is only that it is not
    the provider already in use.
    """
    for provider in ("anthropic", "gemini", "openai"):
        if provider == settings.provider:
            continue
        client = _make(provider, settings)
        if client is not None:
            return client
    return None
