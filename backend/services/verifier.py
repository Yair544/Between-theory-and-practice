"""
Grounding verification: check the model's homework.

Two distinct failures are looked for, and they mean different things:

  invalid citation - the model cited [E42] when the input stops at [E31]. The
                     reference is fabricated. This is the failure mode that
                     makes a hallucination look rigorous, so it is reported
                     loudly and shown in red in the UI.

  unsupported claim - a statement that should carry a citation and carries none.
                      Less alarming, but it is exactly the kind of confident
                      sentence a reader will absorb without checking.

What this does NOT check is whether the cited evidence actually means what the
model says it means. A claim can cite a real line and still misread it. The
score is called `grounding_score`, not `accuracy`, for that reason, and the UI
repeats the distinction.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models import InvalidCitation, UnsupportedClaim, Verification


@dataclass
class Claim:
    """One checkable statement pulled out of the model's response."""

    statement: str
    where: str
    citations: list[str]
    requires_citation: bool


def _collect(payload: dict) -> list[Claim]:
    """Walk the model output and pull out everything that can be checked."""
    claims: list[Claim] = []

    summary = payload.get("summary") or {}
    if summary.get("text"):
        claims.append(Claim(
            statement=summary["text"],
            where="summary",
            citations=list(summary.get("citations") or []),
            requires_citation=True,
        ))

    for index, fact in enumerate(payload.get("facts") or [], start=1):
        claims.append(Claim(
            statement=fact.get("statement", ""),
            where=f"facts[{index}]",
            citations=list(fact.get("evidence") or []),
            # A "fact" with no evidence is a contradiction in terms.
            requires_citation=True,
        ))

    for index, hypothesis in enumerate(payload.get("hypotheses") or [], start=1):
        label = hypothesis.get("title", f"hypothesis {index}")
        claims.append(Claim(
            statement=label,
            where=f"hypotheses[{index}].supporting_evidence",
            citations=list(hypothesis.get("supporting_evidence") or []),
            requires_citation=True,
        ))
        # Contradicting evidence may legitimately be empty - that is a claim
        # about the world, not a missing citation - but if IDs are given they
        # still have to exist.
        claims.append(Claim(
            statement=label,
            where=f"hypotheses[{index}].contradicting_evidence",
            citations=list(hypothesis.get("contradicting_evidence") or []),
            requires_citation=False,
        ))

    for index, event in enumerate(payload.get("inferred_timeline") or [], start=1):
        claims.append(Claim(
            statement=event.get("label", ""),
            where=f"inferred_timeline[{index}]",
            citations=list(event.get("evidence") or []),
            requires_citation=True,
        ))

    for index, action in enumerate(payload.get("next_actions") or [], start=1):
        claims.append(Claim(
            statement=action.get("action", ""),
            where=f"next_actions[{index}]",
            citations=list(action.get("evidence") or []),
            # Some good advice is general ("capture a heap dump before
            # restarting"). We record it as ungrounded and let the UI mark it
            # as generic rather than treating it as a defect.
            requires_citation=False,
        ))

    for index, risk in enumerate(payload.get("reasoning_risks") or [], start=1):
        claims.append(Claim(
            statement=risk.get("where", ""),
            where=f"reasoning_risks[{index}]",
            citations=list(risk.get("evidence") or []),
            requires_citation=False,
        ))

    return claims


def verify(payload: dict, known_ids: set[str]) -> Verification:
    """Run the grounding check over a model response."""
    claims = _collect(payload)

    unsupported: list[UnsupportedClaim] = []
    invalid: list[InvalidCitation] = []
    failed_claims = 0

    for claim in claims:
        bad = [cite for cite in claim.citations if cite not in known_ids]
        for cite in bad:
            invalid.append(InvalidCitation(citation=cite, where=claim.where))

        missing = claim.requires_citation and not claim.citations
        if missing:
            unsupported.append(UnsupportedClaim(
                statement=claim.statement[:400],
                where=claim.where,
            ))

        if bad or missing:
            failed_claims += 1

    checked = len(claims)
    score = 1.0 if checked == 0 else round(1.0 - failed_claims / checked, 3)

    return Verification(
        claims_checked=checked,
        unsupported=unsupported,
        invalid_citations=invalid,
        grounding_score=max(0.0, min(1.0, score)),
    )


def strip_invalid_citations(payload: dict, known_ids: set[str]) -> int:
    """
    Remove fabricated IDs from the payload so the UI never renders a link to a
    line that does not exist.

    The removal count is returned and the originals are preserved in the
    Verification report — deleting them without recording them would hide the
    exact failure the report exists to surface.
    """
    removed = 0

    def clean(container: dict, key: str) -> None:
        nonlocal removed
        values = container.get(key)
        if not isinstance(values, list):
            return
        kept = [value for value in values if value in known_ids]
        removed += len(values) - len(kept)
        container[key] = kept

    summary = payload.get("summary")
    if isinstance(summary, dict):
        clean(summary, "citations")

    for fact in payload.get("facts") or []:
        clean(fact, "evidence")
    for event in payload.get("inferred_timeline") or []:
        clean(event, "evidence")
    for action in payload.get("next_actions") or []:
        clean(action, "evidence")
    for risk in payload.get("reasoning_risks") or []:
        clean(risk, "evidence")
    for hypothesis in payload.get("hypotheses") or []:
        clean(hypothesis, "supporting_evidence")
        clean(hypothesis, "contradicting_evidence")

    return removed
