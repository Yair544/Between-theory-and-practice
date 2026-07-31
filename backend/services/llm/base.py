"""
Provider-neutral interface for a single model call.

Everything above this layer works with `LLMResult`; nothing above it imports a
vendor SDK. That is what makes the "compare two models on the same prompt"
experiment in docs/PROMPTS.md a configuration change rather than a rewrite.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Protocol


class LLMError(RuntimeError):
    """Any provider failure, already translated into something readable."""


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    duration_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    warnings: list[str] = field(default_factory=list)


class LLMClient(Protocol):
    """The only shape the analyser knows about."""

    provider: str
    model: str

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        json_schema: dict | None = None,
    ) -> LLMResult:
        ...


# --- JSON recovery ----------------------------------------------------------
# Structured output is requested from every provider, but a model can still
# return prose around the object, or stop mid-token when it hits max_tokens.
# Failing the whole analysis because of a stray code fence would be a poor
# trade, so parsing is tolerant - and every repair is reported as a warning
# rather than hidden, since silent repairs are how you stop noticing that a
# prompt has quietly stopped working.

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


def parse_json_object(text: str) -> tuple[dict, list[str]]:
    """
    Extract a JSON object from a model response.

    Returns the object and a list of warnings describing any repair applied.
    Raises LLMError if nothing usable can be recovered.
    """
    warnings: list[str] = []
    if not text or not text.strip():
        raise LLMError("The model returned an empty response.")

    candidate = text.strip()

    try:
        return json.loads(candidate), warnings
    except json.JSONDecodeError:
        pass

    stripped = _FENCE.sub("", candidate).strip()
    if stripped != candidate:
        warnings.append("Response was wrapped in a Markdown code fence; unwrapped it.")
        try:
            return json.loads(stripped), warnings
        except json.JSONDecodeError:
            candidate = stripped

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end > start:
        warnings.append("Response contained prose around the JSON object; extracted the object.")
        try:
            return json.loads(candidate[start : end + 1]), warnings
        except json.JSONDecodeError:
            pass

    raise LLMError(
        "The model did not return valid JSON. This usually means the response was "
        "cut off by the output-token limit — try a smaller input or raise "
        "MAX_OUTPUT_TOKENS in .env."
    )
