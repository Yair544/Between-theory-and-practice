"""
Deterministic reasoning-risk detectors.

Asking a model to audit its own reasoning for bias is useful but circular: the
same process that produced the biased conclusion is being asked to notice it.
These rules are the independent check. They look only at the *shape* of the
analysis - how many citations, how confident, which evidence is cited and which
is ignored - so they cannot be talked out of a finding.

Results are merged with the model's own audit. Where both agree the risk is
labelled "rule + model", which is the strongest signal the tool can produce.
"""

from __future__ import annotations

import re
from collections import Counter

from ..models import Evidence, ReasoningRisk
from .biases import name_of

# Causes an engineer reaches for from memory rather than from this incident.
_STOCK_CAUSES = re.compile(
    r"\b(memory leak|dns|thundering herd|garbage collect\w*|gc pause|"
    r"cache stampede|noisy neighbou?r|clock skew|disk full)\b",
    re.I,
)

_DEPLOY_WORDS = re.compile(r"\b(deploy\w*|release|rollout|version|v\d+\.\d+|config change)\b", re.I)

_HINDSIGHT_WORDS = re.compile(
    r"\b(obviously|clearly|as expected|unsurprisingly|of course|it was always)\b", re.I
)

_VARIABLE = re.compile(r"\b(?:[0-9a-f]{8,}|\d+(?:\.\d+)?(?:ms|s|%)?)\b", re.I)


def _shape(text: str) -> str:
    first = text.splitlines()[0] if text else ""
    return _VARIABLE.sub("#", first).strip().lower()[:160]


def _risk(bias: str, where: str, impact: str, mitigation: str,
          severity: str = "medium", evidence: list[str] | None = None) -> dict:
    return {
        "bias": bias,
        "name": name_of(bias),
        "where": where,
        "impact": impact,
        "mitigation": mitigation,
        "severity": severity,
        "detected_by": "heuristic",
        "evidence": evidence or [],
    }


def detect(
    *,
    hypotheses: list[dict],
    evidence: list[Evidence],
    summary_text: str,
    verification_failed: bool,
    offline: bool,
) -> list[dict]:
    """Run every rule and return the findings, most severe first."""
    findings: list[dict] = []
    if not hypotheses:
        return findings

    ordered = sorted(hypotheses, key=lambda h: h.get("confidence", 0), reverse=True)
    leader = ordered[0]
    by_id = {item.id: item for item in evidence}
    total_evidence = len(evidence)

    # --- confirmation bias -------------------------------------------------
    one_sided = [
        h for h in ordered
        if len(h.get("supporting_evidence") or []) >= 2
        and not (h.get("contradicting_evidence") or [])
    ]
    if one_sided:
        titles = ", ".join(f'"{h.get("title", "?")}"' for h in one_sided[:3])
        findings.append(_risk(
            "confirmation_bias",
            f"{len(one_sided)} hypothesis/es list supporting evidence but nothing "
            f"contradicting: {titles}.",
            "Evidence that would weaken the favoured explanation was never collected, "
            "so its confidence score reflects the search, not the world.",
            "For each one, state what you would expect to see in the logs if it were "
            "false, then go and look for it.",
            severity="high" if leader in one_sided else "medium",
            evidence=list(leader.get("supporting_evidence") or [])[:4],
        ))

    # --- post hoc ----------------------------------------------------------
    leader_text = f"{leader.get('title', '')} {leader.get('explanation', '')}"
    if _DEPLOY_WORDS.search(leader_text):
        cited = [by_id[i] for i in (leader.get("supporting_evidence") or []) if i in by_id]
        sources = {item.source for item in cited}
        if cited and sources <= {"deploy_notes", "description"}:
            findings.append(_risk(
                "post_hoc",
                f'The leading hypothesis ("{leader.get("title", "?")}") blames a deployment, '
                "and every item it cites is a deployment note or the incident description - "
                "no log or error line links the deployment to the failure.",
                "Ordering is being read as causation. A deployment that happened before the "
                "incident is a lead, not a cause.",
                "Find a log line that shows the changed code path failing, or check whether "
                "the same error existed before the deploy.",
                severity="high",
                evidence=[item.id for item in cited][:4],
            ))

    # --- overconfidence ----------------------------------------------------
    for hypothesis in ordered:
        confidence = hypothesis.get("confidence") or 0
        support = len(hypothesis.get("supporting_evidence") or [])
        if confidence >= 0.75 and support < 3:
            findings.append(_risk(
                "overconfidence_bias",
                f'"{hypothesis.get("title", "?")}" is rated {confidence:.0%} on {support} '
                "piece(s) of evidence.",
                "A confidence figure this high on this little evidence will be read as "
                "near-certainty by anyone skimming the report.",
                "Either find more corroborating evidence or lower the score. Run the "
                "recommended test before acting on it.",
                severity="high" if confidence >= 0.85 else "medium",
                evidence=list(hypothesis.get("supporting_evidence") or []),
            ))
            break  # one instance is enough to make the point

    # --- anchoring ---------------------------------------------------------
    if total_evidence >= 10:
        cited_indexes = [
            int(cite[1:]) for cite in (leader.get("supporting_evidence") or [])
            if cite.startswith("E") and cite[1:].isdigit()
        ]
        early_cutoff = max(3, total_evidence // 5)
        if cited_indexes and max(cited_indexes) <= early_cutoff:
            findings.append(_risk(
                "anchoring_bias",
                f"The leading hypothesis cites only evidence from the first {early_cutoff} "
                f"of {total_evidence} items.",
                "The first error message shaped the conclusion, and the rest of the "
                "evidence was never used to challenge it.",
                "Read the last third of the evidence first, then re-rank the hypotheses.",
                severity="medium",
                evidence=[f"E{i}" for i in sorted(cited_indexes)[:4]],
            ))

    # --- base-rate neglect -------------------------------------------------
    shapes = Counter(_shape(item.text) for item in evidence)
    dominant = [shape for shape, count in shapes.items() if count >= 5 and shape]
    if dominant:
        all_cited = {
            cite
            for hypothesis in ordered
            for cite in (hypothesis.get("supporting_evidence") or [])
        }
        cited_shapes = {_shape(by_id[i].text) for i in all_cited if i in by_id}
        ignored = [shape for shape in dominant if shape not in cited_shapes]
        if ignored:
            example = ignored[0]
            example_ids = [item.id for item in evidence if _shape(item.text) == example][:4]
            findings.append(_risk(
                "base_rate_neglect",
                f"A pattern that repeats {shapes[example]} times in the input is not cited "
                "by any hypothesis.",
                "The most common signal in the data is being ignored in favour of rarer, "
                "more interesting ones. Common causes are common.",
                "Explain the repeated pattern first. If it is unrelated noise, say so "
                "explicitly rather than passing over it.",
                severity="medium",
                evidence=example_ids,
            ))

    # --- availability ------------------------------------------------------
    for hypothesis in ordered:
        match = _STOCK_CAUSES.search(f"{hypothesis.get('title', '')} {hypothesis.get('explanation', '')}")
        if not match:
            continue
        phrase = match.group(0).lower()
        mentioned_in_input = any(phrase in item.text.lower() for item in evidence)
        if not mentioned_in_input:
            findings.append(_risk(
                "availability_bias",
                f'"{hypothesis.get("title", "?")}" invokes "{match.group(0)}", a phrase that '
                "appears nowhere in the input.",
                "A familiar failure mode is being imported from past experience rather than "
                "derived from this incident's evidence.",
                "Name the specific observation in this incident that points at it, or drop it.",
                severity="medium",
                evidence=[],
            ))
            break

    # --- hindsight ---------------------------------------------------------
    hindsight_source = " ".join(
        [summary_text] + [h.get("explanation", "") for h in ordered]
    )
    match = _HINDSIGHT_WORDS.search(hindsight_source)
    if match:
        findings.append(_risk(
            "hindsight_bias",
            f'The analysis uses "{match.group(0)}" about a cause that was not known when '
            "the incident started.",
            "Framing the answer as having been obvious discourages anyone from questioning "
            "it, and makes the investigation look easier than it was.",
            "Remove certainty language that describes the process rather than the evidence.",
            severity="low",
            evidence=[],
        ))

    # --- automation bias ---------------------------------------------------
    # Not a property of the text - a property of the reader. Raised when the
    # output has the exact shape that invites uncritical acceptance.
    if not offline and (leader.get("confidence") or 0) >= 0.6 and verification_failed:
        findings.append(_risk(
            "automation_bias",
            "The leading hypothesis is presented confidently, but part of this analysis "
            "failed the grounding check.",
            "A fluent, well-structured answer is persuasive whether or not it is correct. "
            "The parts that failed verification read exactly like the parts that passed.",
            "Check the flagged claims against the raw evidence yourself before acting on "
            "any of this.",
            severity="high",
            evidence=[],
        ))

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda risk: order.get(risk["severity"], 5))
    return findings


def merge(model_risks: list[dict], heuristic_risks: list[dict]) -> list[ReasoningRisk]:
    """
    Combine the model's self-audit with the rule-based findings.

    A bias flagged by both gets `detected_by="both"` and keeps the rule's
    wording, because the rule can point at a specific structural fact while the
    model's version tends toward the general.
    """
    by_bias: dict[str, dict] = {}

    for risk in model_risks:
        bias = risk.get("bias")
        if not bias:
            continue
        by_bias[bias] = {
            "bias": bias,
            "name": name_of(bias),
            "where": risk.get("where", ""),
            "impact": risk.get("impact", ""),
            "mitigation": risk.get("mitigation", ""),
            "severity": risk.get("severity", "medium"),
            "detected_by": "model",
            "evidence": list(risk.get("evidence") or []),
        }

    for risk in heuristic_risks:
        bias = risk["bias"]
        if bias in by_bias:
            merged = dict(risk)
            merged["detected_by"] = "both"
            # Keep the model's mitigation if the rule has nothing better to say.
            merged["mitigation"] = risk["mitigation"] or by_bias[bias]["mitigation"]
            by_bias[bias] = merged
        else:
            by_bias[bias] = risk

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    results = sorted(by_bias.values(), key=lambda risk: order.get(risk["severity"], 5))

    return [
        ReasoningRisk(id=f"R{index}", **risk)
        for index, risk in enumerate(results, start=1)
    ]
