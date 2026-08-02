"""
Postmortem rendering.

The document is generated from the analysis, so it inherits the analysis's
uncertainty. It says so at the top, keeps facts and assumptions in separate
sections, and prints the verification result rather than burying it — a
postmortem that hides how much of itself is unverified is worse than no
postmortem, because it launders guesses into the record.
"""

from __future__ import annotations

from ..models import Analysis


def _cites(ids: list[str]) -> str:
    return f" `[{', '.join(ids)}]`" if ids else " _(no evidence cited)_"


def _confidence_label(value: float) -> str:
    if value >= 0.7:
        return "well supported"
    if value >= 0.45:
        return "plausible"
    if value >= 0.2:
        return "weak"
    return "speculative"


def build_markdown(analysis: Analysis) -> str:
    out: list[str] = []
    add = out.append

    meta = analysis.meta

    add(f"# Incident postmortem (DRAFT): {analysis.title}")
    add("")
    add("> **This is a draft produced by IncidentIQ, not a reviewed postmortem.**")
    add("> The root cause below has *not* been confirmed. Every hypothesis needs its")
    add("> recommended test run before any of this is treated as settled.")
    add("")
    add(f"- Generated: {meta.created_at}")
    add(f"- Engine: {'offline deterministic engine (no model used)' if meta.offline else f'{meta.provider} / {meta.model}'}")
    add(f"- Evidence items: {len(analysis.evidence)}")
    add(f"- Grounding: {analysis.verification.grounding_score:.0%} of checkable claims cite valid evidence")
    add("")

    if meta.warnings:
        add("## Warnings from this run")
        add("")
        for warning in meta.warnings:
            add(f"- {warning}")
        add("")

    # --- summary -----------------------------------------------------------
    add("## Summary")
    add("")
    add(analysis.summary.text or "_No summary produced._")
    if analysis.summary.citations:
        add("")
        add(f"Evidence:{_cites(analysis.summary.citations)}")
    add("")

    if analysis.summary.audiences:
        add("### For non-technical readers")
        add("")
        for role, text in analysis.summary.audiences.items():
            if role == "engineer":
                continue
            add(f"**{role.title()}:** {text}")
            add("")

    # --- timeline ----------------------------------------------------------
    add("## Timeline")
    add("")
    if analysis.timeline:
        add("| Time | Event | Source | Evidence |")
        add("|---|---|---|---|")
        for event in analysis.timeline:
            kind = "inferred" if event.inferred else "observed"
            label = event.label.replace("|", "\\|")[:120]
            add(f"| {event.timestamp or '—'} | {label} | {kind} | {', '.join(event.evidence) or '—'} |")
    else:
        add("_No timestamped events could be reconstructed from the input._")
    add("")

    # --- facts / assumptions ----------------------------------------------
    add("## What we know")
    add("")
    if analysis.facts:
        for fact in analysis.facts:
            add(f"- {fact.statement}{_cites(fact.evidence)}")
    else:
        add("_Nothing in this analysis was fully grounded in the input._")
    add("")

    add("## What we are assuming")
    add("")
    if analysis.assumptions:
        for assumption in analysis.assumptions:
            add(f"- **{assumption.statement}**")
            if assumption.why:
                add(f"  - Why: {assumption.why}")
            if assumption.how_to_verify:
                add(f"  - To verify: {assumption.how_to_verify}")
    else:
        add("_No assumptions were recorded. That is unusual; check whether some slipped")
        add("into the facts section above._")
    add("")

    # --- hypotheses --------------------------------------------------------
    add("## Candidate root causes")
    add("")
    add("Ranked by how much of the evidence each one accounts for. **None is confirmed.**")
    add("")
    for index, hypothesis in enumerate(analysis.hypotheses, start=1):
        add(f"### {index}. {hypothesis.title}")
        add("")
        add(f"*Confidence: {hypothesis.confidence:.0%} ({_confidence_label(hypothesis.confidence)})*")
        add("")
        add(hypothesis.explanation)
        add("")
        add(f"- Evidence for:{_cites(hypothesis.supporting_evidence)}")
        against = _cites(hypothesis.contradicting_evidence) if hypothesis.contradicting_evidence \
            else " _(none found — note that this may mean nobody looked)_"
        add(f"- Evidence against:{against}")
        if hypothesis.recommended_test:
            add(f"- **Test that would settle it:** {hypothesis.recommended_test}")
        if hypothesis.rebuttal:
            add("")
            add(f"> **Counter-argument:** {hypothesis.rebuttal}")
        add("")

    # --- reasoning risks ---------------------------------------------------
    add("## Reasoning risks in this investigation")
    add("")
    if analysis.reasoning_risks:
        add("These describe how *this analysis* may be going wrong, not what broke in production.")
        add("")
        for risk in analysis.reasoning_risks:
            add(f"### {risk.name} ({risk.severity}, detected by {risk.detected_by})")
            add("")
            add(f"- Where: {risk.where}")
            if risk.impact:
                add(f"- Effect: {risk.impact}")
            if risk.mitigation:
                add(f"- Reduce it by: {risk.mitigation}")
            add("")
    else:
        add("No reasoning risks were flagged. The detectors ran; they only see reasoning")
        add("that was written down, so this is weaker evidence than it appears.")
        add("")

    # --- actions -----------------------------------------------------------
    add("## Next steps")
    add("")
    if analysis.next_actions:
        add("| Priority | Action | Owner | Because of |")
        add("|---|---|---|---|")
        for action in analysis.next_actions:
            text = action.action.replace("|", "\\|")
            add(f"| {action.priority} | {text} | {action.owner_role} | "
                f"{', '.join(action.evidence) or 'general practice'} |")
    else:
        add("_No actions were produced._")
    add("")

    # --- open questions ----------------------------------------------------
    if analysis.open_questions:
        add("## Open questions")
        add("")
        for question in analysis.open_questions:
            add(f"- {question.question}")
            if question.why_it_matters:
                add(f"  - Why it matters: {question.why_it_matters}")
        add("")

    # --- verification ------------------------------------------------------
    verification = analysis.verification
    add("## Verification of AI claims")
    add("")
    add(f"- Claims checked: {verification.claims_checked}")
    add(f"- Grounding score: {verification.grounding_score:.0%}")
    add(f"- Statements with no citation: {len(verification.unsupported)}")
    add(f"- Citations pointing at non-existent evidence: {len(verification.invalid_citations)}")
    add("")
    if verification.invalid_citations:
        add("**Fabricated citations found in this run:**")
        add("")
        for item in verification.invalid_citations:
            add(f"- `{item.citation}` cited at `{item.where}` — no such evidence item exists.")
        add("")
    if verification.unsupported:
        add("**Statements that cite nothing:**")
        add("")
        for item in verification.unsupported:
            add(f"- _{item.statement[:200]}_ (`{item.where}`)")
        add("")
    add("Grounding measures traceability, not correctness: a claim can cite a real line")
    add("and still misread it.")
    add("")
    add("---")
    add("")
    add("_Generated by IncidentIQ. Review, edit and sign before circulating._")

    return "\n".join(out)
