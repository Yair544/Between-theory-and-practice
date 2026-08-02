"""
The grounding verifier.

These are the tests that matter most in this project: the verifier is the only
thing standing between a fluent hallucination and a report that looks
authoritative.
"""

from __future__ import annotations

from backend.services.verifier import strip_invalid_citations, verify

KNOWN = {"E1", "E2", "E3"}


def payload(**overrides) -> dict:
    base = {
        "summary": {"text": "Checkout failed.", "citations": ["E1"]},
        "facts": [{"statement": "Errors began at 10:14.", "evidence": ["E1"]}],
        "hypotheses": [{
            "title": "Pool exhaustion",
            "explanation": "...",
            "confidence": 0.6,
            "supporting_evidence": ["E2"],
            "contradicting_evidence": ["E3"],
            "recommended_test": "...",
        }],
        "next_actions": [],
        "reasoning_risks": [],
        "inferred_timeline": [],
    }
    base.update(overrides)
    return base


def test_clean_payload_scores_one():
    result = verify(payload(), KNOWN)
    assert result.grounding_score == 1.0
    assert result.unsupported == []
    assert result.invalid_citations == []


def test_fabricated_citation_is_caught():
    """The failure mode that makes a hallucination look rigorous."""
    result = verify(payload(summary={"text": "Checkout failed.", "citations": ["E99"]}), KNOWN)
    assert [c.citation for c in result.invalid_citations] == ["E99"]
    assert result.invalid_citations[0].where == "summary"
    assert result.grounding_score < 1.0


def test_fact_without_evidence_is_unsupported():
    result = verify(payload(facts=[{"statement": "The database was the cause.", "evidence": []}]), KNOWN)
    assert len(result.unsupported) == 1
    assert result.unsupported[0].where == "facts[1]"


def test_empty_contradicting_list_is_not_a_violation():
    """
    "I found nothing that contradicts this" is a claim about the world, not a
    missing citation. The hypotheses view warns about it separately.
    """
    hypothesis = payload()["hypotheses"][0] | {"contradicting_evidence": []}
    result = verify(payload(hypotheses=[hypothesis]), KNOWN)
    assert result.unsupported == []
    assert result.grounding_score == 1.0


def test_generic_action_is_recorded_but_not_penalised():
    """Some advice is legitimately general; the UI marks it rather than failing it."""
    result = verify(payload(next_actions=[
        {"action": "Capture a heap dump before restarting.", "evidence": []},
    ]), KNOWN)
    assert result.grounding_score == 1.0


def test_score_is_the_share_of_failing_claims():
    result = verify(payload(
        summary={"text": "x", "citations": []},              # unsupported
        facts=[{"statement": "y", "evidence": ["E7"]}],      # invalid citation
    ), KNOWN)
    # 4 claims collected: summary, 1 fact, 2 hypothesis slots. 2 of them failed.
    assert result.claims_checked == 4
    assert result.grounding_score == 0.5


def test_strip_removes_fake_ids_but_keeps_real_ones():
    data = payload(
        summary={"text": "x", "citations": ["E1", "E42"]},
        facts=[{"statement": "y", "evidence": ["E99"]}],
    )
    removed = strip_invalid_citations(data, KNOWN)
    assert removed == 2
    assert data["summary"]["citations"] == ["E1"]
    assert data["facts"][0]["evidence"] == []


def test_strip_runs_after_verify_so_the_report_still_names_them():
    """
    Order matters in the pipeline: verify first, then strip. Otherwise the
    fabricated citations disappear from the record that exists to expose them.
    """
    data = payload(summary={"text": "x", "citations": ["E42"]})
    result = verify(data, KNOWN)
    strip_invalid_citations(data, KNOWN)
    assert result.invalid_citations[0].citation == "E42"
    assert data["summary"]["citations"] == []
