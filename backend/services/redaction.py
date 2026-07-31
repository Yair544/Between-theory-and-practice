"""
Redaction of secret-shaped values before anything is sent to a model provider.

The brief asks "what information should not be sent to external AI APIs?".
This module is our answer in code rather than in prose. It runs before the
prompt is built, so a redacted value never exists in any outbound request.

Two deliberate limitations, stated here because pretending otherwise would be
worse than the gap itself:

1. This is pattern matching, not classification. It catches values with a
   recognisable *shape* (an email, a JWT, a card number). It cannot recognise
   that "customer 88213 requested deletion" is personal data.
2. Redaction changes what the model sees. A log line reading
   "auth failed for [REDACTED_EMAIL]" loses the fact that all failures shared
   one address. We accept the loss; the alternative is exfiltrating user data
   to a third party to slightly improve a debugging suggestion.
"""

from __future__ import annotations

import re

# Order matters: the most specific patterns run first so a JWT is not first
# mangled by the generic long-token rule.
_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b"),
        "[REDACTED_JWT]",
    ),
    (
        "provider_key",
        re.compile(r"\b(?:sk-[A-Za-z0-9_\-]{16,}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9\-]{10,})\b"),
        "[REDACTED_KEY]",
    ),
    (
        "auth_header",
        re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._\-+/=]{12,}"),
        "[REDACTED_AUTH]",
    ),
    (
        "assigned_secret",
        # password=..., api_key: ..., token = "..."
        re.compile(
            r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|apikey|access[_-]?token|token)"
            r"\s*[:=]\s*\"?[^\s\"',;]{4,}\"?"
        ),
        r"\1=[REDACTED]",
    ),
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    (
        "card",
        re.compile(r"\b(?:\d{4}[ \-]?){3}\d{3,4}\b"),
        "[REDACTED_CARD]",
    ),
    (
        "ipv4",
        # Private ranges are usually the interesting ones in an incident, so we
        # keep 10.x / 192.168.x / 127.x and only redact routable addresses,
        # which are the ones that can identify a real person or customer.
        re.compile(
            r"\b(?!10\.)(?!127\.)(?!192\.168\.)(?!172\.(?:1[6-9]|2\d|3[01])\.)"
            r"(?:\d{1,3}\.){3}\d{1,3}\b"
        ),
        "[REDACTED_IP]",
    ),
]


def redact(text: str) -> tuple[str, int]:
    """
    Replace secret-shaped substrings.

    Returns the cleaned text and the number of replacements, which the UI shows
    so the user knows redaction actually happened rather than trusting a
    checkbox.
    """
    if not text:
        return text, 0

    total = 0
    result = text
    for _name, pattern, replacement in _PATTERNS:
        result, count = pattern.subn(replacement, result)
        total += count
    return result, total


def redact_mapping(sources: dict[str, str]) -> tuple[dict[str, str], int]:
    """Redact every source blob, returning the total replacement count."""
    cleaned: dict[str, str] = {}
    total = 0
    for key, value in sources.items():
        cleaned[key], count = redact(value)
        total += count
    return cleaned, total
