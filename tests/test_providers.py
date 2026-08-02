"""
Provider selection and the offline rule.

No network here either. These tests only check which client gets built for a
given configuration, which is the logic most likely to break silently: a
mis-wired provider does not crash, it quietly falls back to the offline engine
and produces a weaker analysis that still looks like a real one.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from backend.config import PROVIDERS, load_settings
from backend.services.llm import build_alternate_client, build_client


@pytest.fixture
def blank():
    """Settings with every key cleared, whatever the developer's .env says."""
    return replace(
        load_settings(),
        anthropic_api_key="",
        gemini_api_key="",
        openai_api_key="",
    )


# --- the offline rule --------------------------------------------------------

def test_gemini_is_the_default_provider(blank):
    assert blank.provider == "gemini"
    assert blank.gemini_model == "gemini-2.5-flash"


def test_missing_key_means_offline(blank):
    for provider in ("gemini", "anthropic", "openai"):
        assert replace(blank, provider=provider).offline is True


def test_a_key_takes_the_matching_provider_online(blank):
    assert replace(blank, provider="gemini", gemini_api_key="AIza-x").offline is False


def test_a_key_for_a_different_provider_does_not_count(blank):
    """The commonest misconfiguration: right key, wrong LLM_PROVIDER."""
    settings = replace(blank, provider="gemini", anthropic_api_key="sk-ant-x")
    assert settings.offline is True


def test_offline_provider_ignores_every_key(blank):
    settings = replace(blank, provider="offline", gemini_api_key="AIza-x")
    assert settings.offline is True
    assert build_client(settings) is None


def test_active_model_follows_the_provider(blank):
    assert replace(blank, provider="gemini").active_model == blank.gemini_model
    assert replace(blank, provider="anthropic").active_model == blank.anthropic_model
    assert replace(blank, provider="offline").active_model == "deterministic-engine"


# --- what describe() is allowed to expose ------------------------------------

def test_describe_reports_key_presence_never_key_value(blank):
    settings = replace(blank, provider="gemini", gemini_api_key="AIza-super-secret")
    described = settings.describe()

    assert described["has_gemini_key"] is True
    assert set(described) >= {"has_anthropic_key", "has_gemini_key", "has_openai_key"}
    assert "AIza-super-secret" not in str(described), (
        "a key must never cross the boundary to the browser"
    )


# --- client construction -----------------------------------------------------

def test_build_client_returns_none_when_the_key_is_missing(blank):
    assert build_client(replace(blank, provider="gemini")) is None


def test_build_client_constructs_the_configured_provider(blank):
    settings = replace(blank, provider="gemini", gemini_api_key="AIza-x")
    client = build_client(settings)
    assert client is not None
    assert client.provider == "gemini"
    assert client.model == "gemini-2.5-flash"


def test_alternate_client_is_a_different_provider(blank):
    """compare_models.py depends on this: never the provider already in use."""
    settings = replace(
        blank, provider="gemini", gemini_api_key="AIza-x", anthropic_api_key="sk-ant-x"
    )
    alternate = build_alternate_client(settings)
    assert alternate is not None
    assert alternate.provider == "anthropic"


def test_alternate_client_is_none_when_only_one_provider_has_a_key(blank):
    settings = replace(blank, provider="gemini", gemini_api_key="AIza-x")
    assert build_alternate_client(settings) is None


def test_every_advertised_provider_is_constructible(blank):
    """PROVIDERS is the list the config validates against; keep them in step."""
    for provider in PROVIDERS:
        if provider == "offline":
            continue
        settings = replace(
            blank,
            provider=provider,
            **{f"{provider}_api_key": "test-key"},
        )
        client = build_client(settings)
        assert client is not None, f"{provider} is advertised but does not build"
        assert client.provider == provider
