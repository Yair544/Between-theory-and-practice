"""
Configuration, loaded once from the environment.

Reading configuration in exactly one place means the rest of the codebase never
touches os.environ, and the offline-mode decision is made here rather than being
re-derived (differently) in three separate modules.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
SAMPLES_DIR = ROOT / "data" / "samples"

load_dotenv(ROOT / ".env")


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _str(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


PROVIDERS = ("anthropic", "gemini", "openai", "offline")


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of the environment at process start."""

    provider: str
    anthropic_api_key: str
    anthropic_model: str
    gemini_api_key: str
    gemini_model: str
    openai_api_key: str
    openai_model: str

    max_output_tokens: int
    hypothesis_count: int
    max_input_chars: int
    redact_pii: bool

    host: str
    port: int
    auto_open_browser: bool

    @property
    def _keys(self) -> dict[str, str]:
        return {
            "anthropic": self.anthropic_api_key,
            "gemini": self.gemini_api_key,
            "openai": self.openai_api_key,
        }

    @property
    def offline(self) -> bool:
        """
        True when no language model will be called.

        Either the operator asked for it, or the key for the chosen provider is
        missing. Both cases behave identically, and both are reported to the UI:
        an analysis produced without a model must never be mistaken for one that
        used a model.
        """
        if self.provider == "offline":
            return True
        return not self._keys.get(self.provider)

    @property
    def active_model(self) -> str:
        models = {
            "anthropic": self.anthropic_model,
            "gemini": self.gemini_model,
            "openai": self.openai_model,
        }
        return models.get(self.provider, "deterministic-engine")

    def describe(self) -> dict:
        """Non-secret view of the configuration, safe to send to the browser."""
        return {
            "provider": self.provider,
            "model": self.active_model,
            "offline": self.offline,
            # Booleans only. The key itself must never cross this boundary.
            "has_anthropic_key": bool(self.anthropic_api_key),
            "has_gemini_key": bool(self.gemini_api_key),
            "has_openai_key": bool(self.openai_api_key),
            "redact_pii": self.redact_pii,
            "hypothesis_count": self.hypothesis_count,
            "max_input_chars": self.max_input_chars,
        }


def load_settings() -> Settings:
    provider = _str("LLM_PROVIDER", "gemini").lower()
    if provider not in PROVIDERS:
        provider = "gemini"

    return Settings(
        provider=provider,
        anthropic_api_key=_str("ANTHROPIC_API_KEY"),
        anthropic_model=_str("ANTHROPIC_MODEL", "claude-opus-4-8"),
        gemini_api_key=_str("GEMINI_API_KEY") or _str("GOOGLE_API_KEY"),
        gemini_model=_str("GEMINI_MODEL", "gemini-2.5-flash"),
        openai_api_key=_str("OPENAI_API_KEY"),
        openai_model=_str("OPENAI_MODEL", "gpt-4o"),
        max_output_tokens=_int("MAX_OUTPUT_TOKENS", 16000),
        hypothesis_count=_int("HYPOTHESIS_COUNT", 4),
        max_input_chars=_int("MAX_INPUT_CHARS", 120_000),
        redact_pii=_bool("REDACT_PII", True),
        host=_str("HOST", "127.0.0.1"),
        port=_int("PORT", 8000),
        auto_open_browser=_bool("AUTO_OPEN_BROWSER", True),
    )


settings = load_settings()
