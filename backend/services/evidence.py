"""
Evidence extraction: turn free-text blobs into numbered, citable items.

This runs before any model is involved, and it is the reason the tool can check
the model's work. Because IDs are assigned deterministically here, a citation
like "E14" either resolves to a real input line or it does not — there is no
room for a plausible-sounding reference to a line that was never in the input.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from ..models import Evidence, InputStats

# --- timestamp formats we can recognise -------------------------------------
# Ordered from most to least specific. Anything unmatched simply has no
# timestamp; guessing one would fabricate evidence.
_TIMESTAMP_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)"), "iso_z"),
    (re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?[+\-]\d{2}:?\d{2})"), "iso_offset"),
    (re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"), "iso_naive"),
    (re.compile(r"(\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}:\d{2})"), "eu_slash"),
    (re.compile(r"\[(\d{2}:\d{2}:\d{2})\]"), "time_only"),
]

_SEVERITY_TOKENS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(FATAL|CRITICAL|PANIC|EMERG)\b", re.I), "critical"),
    (re.compile(r"\b(ERROR|ERR|EXCEPTION|FAIL(?:ED|URE)?|TIMEOUT|REFUSED)\b", re.I), "critical"),
    (re.compile(r"\b(WARN(?:ING)?|DEGRADED|RETRY|THROTTL)\b", re.I), "high"),
    (re.compile(r"\b(NOTICE|INFO)\b", re.I), "low"),
    (re.compile(r"\b(DEBUG|TRACE)\b", re.I), "info"),
]

# A traceback is one logical event spread over many lines. Splitting it into
# separate evidence items would let a hypothesis cite line 4 of a stack trace as
# if it were an independent observation.
_TRACE_CONT = re.compile(r"^(\s{2,}|\t|\s*(File \"|at |Caused by:|\.\.\.))")


def _parse_timestamp(line: str) -> str | None:
    """Return an ISO-8601 timestamp if the line begins with a recognisable one."""
    for pattern, kind in _TIMESTAMP_PATTERNS:
        match = pattern.search(line)
        if not match:
            continue
        raw = match.group(1)
        try:
            if kind == "time_only":
                # No date in the line. Anchor to today so ordering works, and
                # accept that the absolute date is meaningless.
                today = datetime.now(timezone.utc).date().isoformat()
                return f"{today}T{raw}"
            if kind == "eu_slash":
                return datetime.strptime(raw, "%d/%m/%Y %H:%M:%S").isoformat()
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).isoformat()
        except ValueError:
            continue
    return None


def _detect_severity(line: str) -> str | None:
    for pattern, severity in _SEVERITY_TOKENS:
        if pattern.search(line):
            return severity
    return None


def _split_records(text: str) -> list[tuple[int, str]]:
    """
    Split a blob into logical records, keeping stack-trace continuations
    attached to the line that started them. Returns (line_number, record).
    """
    records: list[tuple[int, str]] = []
    for index, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        if records and _TRACE_CONT.match(raw):
            number, previous = records[-1]
            records[-1] = (number, f"{previous}\n{raw.rstrip()}")
        else:
            records.append((index, raw.rstrip()))
    return records


def extract_evidence(
    sources: dict[str, str],
    *,
    max_chars: int,
    redacted_count: int = 0,
) -> tuple[list[Evidence], InputStats]:
    """
    Build the evidence list.

    `sources` maps a source key ("logs", "alerts", ...) to already-redacted
    text. Truncation is applied per source rather than to the concatenation, so
    an enormous log file cannot silently push the deployment notes out of the
    analysis entirely.
    """
    items: list[Evidence] = []
    total_chars = sum(len(v) for v in sources.values())
    truncated = False
    counter = 0

    budget_per_source = max(2000, max_chars // max(1, len(sources))) if sources else max_chars

    for source, text in sources.items():
        if len(text) > budget_per_source:
            text = text[:budget_per_source]
            truncated = True

        for line_number, record in _split_records(text):
            counter += 1
            items.append(
                Evidence(
                    id=f"E{counter}",
                    source=source,
                    text=record,
                    line=line_number,
                    timestamp=_parse_timestamp(record),
                    severity=_detect_severity(record),
                )
            )

    stats = InputStats(
        total_chars=total_chars,
        truncated=truncated,
        redacted_count=redacted_count,
        sources=list(sources.keys()),
    )
    return items, stats


def render_for_prompt(evidence: list[Evidence]) -> str:
    """
    Format the evidence list for the model.

    Each item is prefixed with its ID so the model can cite it, and the source
    is included so the model can weigh a deployment note differently from a user
    complaint. Nothing here is summarised: the model sees the same text a human
    reviewer would see when checking a citation.
    """
    lines: list[str] = []
    for item in evidence:
        stamp = f" @ {item.timestamp}" if item.timestamp else ""
        severity = f" [{item.severity}]" if item.severity else ""
        body = item.text.replace("\n", "\n      ")
        lines.append(f"[{item.id}] ({item.source}{stamp}{severity})\n      {body}")
    return "\n".join(lines)


def evidence_ids(evidence: list[Evidence]) -> set[str]:
    return {item.id for item in evidence}
