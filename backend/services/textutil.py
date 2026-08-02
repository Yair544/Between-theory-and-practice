"""
Shared text normalisation.

`message_shape` collapses a log line to its template so that

    2026-05-02T10:15:02Z ERROR HikariPool - timed out after 30000ms
    2026-05-02T10:19:44Z ERROR HikariPool - timed out after 30000ms

are recognised as the same event happening twice rather than as two
independent observations. Three parts of the engine need exactly this
grouping - the timeline, the offline engine and the base-rate detector - and
they were each carrying their own copy, which drifted. One implementation now.

Order matters: the leading timestamp is stripped *before* numbers are blanked,
otherwise the seconds field survives as a distinguishing digit and every line
looks unique.
"""

from __future__ import annotations

import re

_LEADING_TIMESTAMP = re.compile(
    r"^\s*[\[\(]?"
    r"(?:\d{4}-\d{2}-\d{2}[T ])?"          # optional date
    r"\d{1,2}:\d{2}:\d{2}(?:[.,]\d+)?"     # time
    r"\s*(?:Z|[+\-]\d{2}:?\d{2})?"         # optional zone
    r"[\]\)]?\s*"
)

# Anything that varies between two instances of the same event: durations,
# counts, ids, percentages, hex digests.
_VARIABLE = re.compile(r"\b[0-9a-f]{8,}\b|\b\d+(?:\.\d+)?(?:ms|s|%)?\b", re.I)


def message_shape(text: str, *, limit: int = 160) -> str:
    """A normalised form suitable only for grouping. Never shown to the user."""
    first_line = text.splitlines()[0] if text else ""
    without_time = _LEADING_TIMESTAMP.sub("", first_line)
    return _VARIABLE.sub("#", without_time).strip().lower()[:limit]


def first_line(text: str, limit: int = 120) -> str:
    """The human-readable label for an evidence item."""
    line = (text.splitlines()[0] if text else "").strip()
    return line if len(line) <= limit else line[: limit - 1] + "…"
