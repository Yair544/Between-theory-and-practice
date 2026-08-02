"""Evidence extraction, redaction and timeline reconstruction."""

from __future__ import annotations

from backend.services.evidence import extract_evidence, render_for_prompt
from backend.services.redaction import redact
from backend.services.textutil import message_shape
from backend.services.timeline import build_timeline

from .conftest import SAMPLE_LOGS


# --- ids ---------------------------------------------------------------------

def test_ids_are_sequential_and_unique(evidence):
    ids = [item.id for item in evidence]
    assert ids == [f"E{i}" for i in range(1, len(ids) + 1)]
    assert len(set(ids)) == len(ids)


def test_stack_trace_stays_one_item(evidence):
    """
    A traceback is one event. Splitting it would let a hypothesis cite line 4
    of a stack trace as if it were an independent observation.
    """
    trace_items = [item for item in evidence if item.source == "errors"]
    assert len(trace_items) == 1
    assert "SocketTimeoutException" in trace_items[0].text
    assert "PooledGatewayClient.java:114" in trace_items[0].text


# --- timestamps & severity ---------------------------------------------------

def test_timestamps_are_parsed(evidence):
    timed = [item for item in evidence if item.timestamp]
    assert len(timed) == 6  # every log line, none of the trace


def test_unparseable_lines_get_no_timestamp():
    items, _ = extract_evidence({"logs": "something broke, no idea when"}, max_chars=1000)
    assert items[0].timestamp is None, "a guessed timestamp would be fabricated evidence"


def test_severity_detection(evidence):
    severities = [item.severity for item in evidence if item.source == "logs"]
    assert severities[:4] == ["critical"] * 4
    assert severities[4] == "low"    # INFO
    assert severities[5] == "high"   # WARN


# --- truncation --------------------------------------------------------------

def test_truncation_is_per_source_not_global():
    """One huge source must not push a small one out of the analysis entirely."""
    items, stats = extract_evidence(
        {"logs": "x\n" * 20_000, "deploy_notes": "v2.4.1 deployed at 10:02"},
        max_chars=4000,
    )
    assert stats.truncated
    assert any(item.source == "deploy_notes" for item in items)


# --- redaction ---------------------------------------------------------------

def test_redaction_covers_the_documented_shapes():
    text = (
        "user alice@hospital.org failed auth from 203.0.113.9 "
        "with token sk-abcdef0123456789abcdef card 4111 1111 1111 1111"
    )
    cleaned, count = redact(text)
    assert count >= 4
    for secret in ("alice@hospital.org", "203.0.113.9", "sk-abcdef0123456789abcdef", "4111"):
        assert secret not in cleaned


def test_private_ips_are_kept():
    """Internal addresses identify a host, not a person, and they matter for debugging."""
    cleaned, _ = redact("connection refused to 10.0.4.12 and 192.168.1.7")
    assert "10.0.4.12" in cleaned
    assert "192.168.1.7" in cleaned


def test_redaction_survives_evidence_extraction():
    cleaned, _ = redact("2026-05-02T10:00:00Z ERROR login failed for bob@example.com")
    items, _ = extract_evidence({"logs": cleaned}, max_chars=1000)
    assert "bob@example.com" not in items[0].text
    assert items[0].timestamp is not None, "redaction must not break timestamp parsing"


# --- timeline ----------------------------------------------------------------

def test_repeated_lines_collapse_into_one_event(evidence):
    """Three identical pool timeouts are one fact about the incident, not three."""
    events = build_timeline(evidence)
    pool_events = [e for e in events if "HikariPool" in e.label]
    assert len(pool_events) == 1
    assert "Repeated 3 times" in pool_events[0].detail
    assert len(pool_events[0].evidence) == 3


def test_timeline_is_ordered_and_never_inferred(evidence):
    events = build_timeline(evidence)
    stamps = [e.timestamp for e in events]
    assert stamps == sorted(stamps)
    assert all(e.inferred is False for e in events), (
        "the deterministic timeline must never invent an event"
    )


def test_message_shape_ignores_timestamps_and_numbers():
    a = "2026-05-02T10:15:02Z ERROR pool timed out after 30000ms"
    b = "2026-05-02T10:19:44Z ERROR pool timed out after 45000ms"
    assert message_shape(a) == message_shape(b)


# --- prompt rendering --------------------------------------------------------

def test_prompt_block_labels_every_item(evidence):
    block = render_for_prompt(evidence)
    for item in evidence:
        assert f"[{item.id}]" in block, "the model can only cite ids it was shown"
