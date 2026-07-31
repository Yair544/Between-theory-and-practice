"""
Deterministic timeline reconstruction.

This is intentionally dumb. It orders the evidence that carries a timestamp and
collapses repeats; it never invents an event to bridge a gap. Anything the model
adds later is marked `inferred=True`, so the UI can draw the difference.

Building the observed skeleton here rather than asking the model for the whole
timeline also gives us something to check the model against: if the model claims
an event at 10:04 and no evidence item carries that time, that is visible.
"""

from __future__ import annotations

import re
from collections import Counter

from ..models import Evidence, TimelineEvent

# Numbers, hex ids and quoted values differ between otherwise identical log
# lines. Blanking them lets "connection timeout to db-3" and
# "connection timeout to db-7" collapse into one repeated event.
_VARIABLE = re.compile(r"\b(?:[0-9a-f]{8,}|\d+(?:\.\d+)?(?:ms|s|%)?)\b", re.I)


def _shape(text: str) -> str:
    """A normalised form used only for grouping repeats."""
    first_line = text.splitlines()[0] if text else ""
    return _VARIABLE.sub("#", first_line).strip().lower()[:160]


def _label(text: str, limit: int = 120) -> str:
    first_line = text.splitlines()[0].strip()
    return first_line if len(first_line) <= limit else first_line[: limit - 1] + "…"


def build_timeline(evidence: list[Evidence]) -> list[TimelineEvent]:
    """
    Ordered, observed-only events.

    Consecutive items sharing a normalised shape are merged into one event that
    reports how many times it occurred, because forty identical timeout lines
    are one fact about the incident, not forty.
    """
    timed = [item for item in evidence if item.timestamp]
    timed.sort(key=lambda item: (item.timestamp or "", item.id))

    events: list[TimelineEvent] = []
    index = 0
    counter = 0

    while index < len(timed):
        current = timed[index]
        shape = _shape(current.text)

        group = [current]
        lookahead = index + 1
        while lookahead < len(timed) and _shape(timed[lookahead].text) == shape:
            group.append(timed[lookahead])
            lookahead += 1

        counter += 1
        repeats = len(group)
        detail = ""
        if repeats > 1:
            last = group[-1].timestamp
            detail = f"Repeated {repeats} times, through {last}."

        events.append(
            TimelineEvent(
                id=f"T{counter}",
                timestamp=current.timestamp,
                label=_label(current.text),
                detail=detail,
                # Cap the citation list: an event that repeated 200 times does
                # not need 200 pills in the UI.
                evidence=[item.id for item in group[:8]],
                inferred=False,
            )
        )
        index = lookahead

    return events


def coverage(evidence: list[Evidence]) -> dict[str, int]:
    """
    How much of the input could be placed in time.

    Used by the bias detectors: a timeline built from 4 of 300 lines invites
    conclusions the data cannot support.
    """
    total = len(evidence)
    timed = sum(1 for item in evidence if item.timestamp)
    by_source = Counter(item.source for item in evidence)
    return {
        "total_items": total,
        "timed_items": timed,
        "untimed_items": total - timed,
        **{f"source_{key}": value for key, value in by_source.items()},
    }
