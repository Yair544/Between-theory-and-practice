"""
The rule-based bias detectors.

Each test builds the smallest analysis shape that should trigger one rule, and
one that should not. A detector that fires on everything is as useless as one
that never fires.
"""

from __future__ import annotations

from backend.models import Evidence
from backend.services.risk_detector import detect, merge


def ev(id_: str, text: str, source: str = "logs", severity: str = "critical") -> Evidence:
    return Evidence(id=id_, source=source, text=text, severity=severity)


def hyp(**overrides) -> dict:
    base = {
        "title": "Connection pool exhausted",
        "explanation": "The pool ran out of connections.",
        "confidence": 0.5,
        "supporting_evidence": ["E1", "E2"],
        "contradicting_evidence": ["E3"],
        "recommended_test": "Check pool metrics.",
    }
    base.update(overrides)
    return base


def run(hypotheses, evidence, summary="", verification_failed=False, offline=False):
    return {
        risk["bias"]
        for risk in detect(
            hypotheses=hypotheses,
            evidence=evidence,
            summary_text=summary,
            verification_failed=verification_failed,
            offline=offline,
        )
    }


BASE_EVIDENCE = [ev(f"E{i}", f"line {i} failed") for i in range(1, 4)]


# --- confirmation ------------------------------------------------------------

def test_confirmation_bias_fires_on_a_one_sided_hypothesis():
    found = run([hyp(contradicting_evidence=[])], BASE_EVIDENCE)
    assert "confirmation_bias" in found


def test_confirmation_bias_quiet_when_both_sides_are_present():
    assert "confirmation_bias" not in run([hyp()], BASE_EVIDENCE)


# --- post hoc ----------------------------------------------------------------

def test_post_hoc_fires_when_a_deploy_is_blamed_on_deploy_notes_alone():
    evidence = [ev("E1", "v2.4.1 deployed at 10:02", source="deploy_notes", severity="info")]
    found = run([hyp(
        title="Release v2.4.1 broke checkout",
        supporting_evidence=["E1"],
        contradicting_evidence=["E1"],   # keep confirmation bias out of the result
    )], evidence)
    assert "post_hoc" in found


def test_post_hoc_quiet_when_a_log_line_links_the_deploy_to_the_failure():
    evidence = [
        ev("E1", "v2.4.1 deployed at 10:02", source="deploy_notes", severity="info"),
        ev("E2", "ERROR new pooled client failed: read timeout"),
    ]
    found = run([hyp(
        title="Release v2.4.1 broke checkout",
        supporting_evidence=["E1", "E2"],
        contradicting_evidence=["E2"],
    )], evidence)
    assert "post_hoc" not in found


# --- overconfidence ----------------------------------------------------------

def test_overconfidence_fires_on_high_confidence_and_thin_evidence():
    found = run([hyp(confidence=0.9, supporting_evidence=["E1"])], BASE_EVIDENCE)
    assert "overconfidence_bias" in found


def test_overconfidence_quiet_when_the_evidence_matches_the_claim():
    found = run([hyp(confidence=0.75, supporting_evidence=["E1", "E2", "E3"])], BASE_EVIDENCE)
    assert "overconfidence_bias" not in found


# --- anchoring ---------------------------------------------------------------

def test_anchoring_fires_when_only_the_earliest_evidence_is_cited():
    evidence = [ev(f"E{i}", f"line {i} failed") for i in range(1, 21)]
    found = run([hyp(supporting_evidence=["E1", "E2"])], evidence)
    assert "anchoring_bias" in found


def test_anchoring_quiet_when_later_evidence_is_used():
    evidence = [ev(f"E{i}", f"line {i} failed") for i in range(1, 21)]
    found = run([hyp(supporting_evidence=["E2", "E18"])], evidence)
    assert "anchoring_bias" not in found


# --- base-rate ---------------------------------------------------------------

def test_base_rate_neglect_fires_when_the_dominant_pattern_is_ignored():
    evidence = (
        [ev(f"E{i}", "ERROR pool timed out after 30000ms") for i in range(1, 9)]
        + [ev("E9", "ERROR rare disk parity mismatch")]
    )
    found = run([hyp(supporting_evidence=["E9"], contradicting_evidence=["E9"])], evidence)
    assert "base_rate_neglect" in found


# --- availability ------------------------------------------------------------

def test_availability_bias_fires_on_a_stock_cause_absent_from_the_input():
    found = run([hyp(
        title="Memory leak in the worker",
        supporting_evidence=["E1"],
        contradicting_evidence=["E2"],
    )], BASE_EVIDENCE)
    assert "availability_bias" in found


def test_availability_bias_quiet_when_the_input_actually_says_it():
    evidence = [ev("E1", "ERROR OutOfMemoryError: suspected memory leak in worker pool")]
    found = run([hyp(
        title="Memory leak in the worker",
        supporting_evidence=["E1"],
        contradicting_evidence=["E1"],
    )], evidence)
    assert "availability_bias" not in found


# --- hindsight ---------------------------------------------------------------

def test_hindsight_fires_on_certainty_language():
    found = run([hyp()], BASE_EVIDENCE, summary="The cause was obviously the new pool size.")
    assert "hindsight_bias" in found


# --- automation --------------------------------------------------------------

def test_automation_bias_fires_on_a_confident_but_unverified_answer():
    found = run([hyp(confidence=0.7)], BASE_EVIDENCE, verification_failed=True)
    assert "automation_bias" in found


def test_automation_bias_not_raised_offline():
    """There is no model output to over-trust when no model ran."""
    found = run([hyp(confidence=0.7)], BASE_EVIDENCE, verification_failed=True, offline=True)
    assert "automation_bias" not in found


# --- merge -------------------------------------------------------------------

def test_agreement_between_rule_and_model_is_labelled_both():
    model = [{"bias": "post_hoc", "where": "the model's wording", "impact": "",
              "mitigation": "model mitigation", "severity": "medium"}]
    rules = [{"bias": "post_hoc", "name": "Post hoc fallacy", "where": "the rule's wording",
              "impact": "", "mitigation": "", "severity": "high",
              "detected_by": "heuristic", "evidence": []}]
    merged = merge(model, rules)
    assert len(merged) == 1
    assert merged[0].detected_by == "both"
    assert merged[0].where == "the rule's wording", "the rule can point at something specific"
    assert merged[0].mitigation == "model mitigation", "kept when the rule has nothing better"


def test_findings_are_sorted_by_severity():
    merged = merge([], [
        {"bias": "hindsight_bias", "name": "Hindsight bias", "where": "", "impact": "",
         "mitigation": "", "severity": "low", "detected_by": "heuristic", "evidence": []},
        {"bias": "post_hoc", "name": "Post hoc fallacy", "where": "", "impact": "",
         "mitigation": "", "severity": "high", "detected_by": "heuristic", "evidence": []},
    ])
    assert [risk.severity for risk in merged] == ["high", "low"]
    assert [risk.id for risk in merged] == ["R1", "R2"]
