"""
The offline engine: an analysis with no language model involved.

This is not a stub. It runs whenever no API key is configured, and it does what
can honestly be done with pattern matching alone: group the errors, find the
first and worst occurrences, propose a small number of mechanical hypotheses,
and refuse to write the parts that require judgement.

Two reasons it exists:

1. The tool has to be runnable by someone who has not been given a key - a
   marker, a teammate, a CI job.
2. It is the control condition. Comparing the offline output with the
   model-assisted output on the same incident is what shows what the AI actually
   contributed, which is a question the brief asks directly. In our testing the
   honest answer was: the offline engine finds the error clusters, and the model
   supplies the causal reasoning and the disconfirming evidence.

Everything it produces is marked offline in the response so it can never be
mistaken for model output.
"""

from __future__ import annotations

from collections import Counter

from ..models import Evidence
from .textutil import message_shape as _shape


def analyse(evidence: list[Evidence], *, title: str, hypothesis_count: int) -> dict:
    """Produce a payload in the same shape the model would return."""
    errors = [item for item in evidence if item.severity in {"critical", "high"}]
    shapes = Counter(_shape(item.text) for item in errors)
    top_shapes = shapes.most_common(hypothesis_count)

    ids_for_shape: dict[str, list[str]] = {}
    for item in errors:
        ids_for_shape.setdefault(_shape(item.text), []).append(item.id)

    first_error = errors[0] if errors else None
    deploy_items = [item for item in evidence if item.source == "deploy_notes"]

    # --- summary -----------------------------------------------------------
    if errors:
        summary_text = (
            f"{len(errors)} error-level items were found across "
            f"{len({item.source for item in errors})} source(s), falling into "
            f"{len(shapes)} distinct message pattern(s). The most frequent pattern "
            f"occurred {top_shapes[0][1]} time(s). "
        )
        if first_error and first_error.timestamp:
            summary_text += f"The earliest error is timestamped {first_error.timestamp}. "
        summary_text += (
            "No causal analysis was performed: this summary was produced by pattern "
            "matching, with no language model involved."
        )
        citations = [item.id for item in errors[:5]]
    else:
        summary_text = (
            f"{len(evidence)} evidence items were indexed. None matched an error or "
            "warning pattern, so nothing can be said about what failed without a "
            "language model or a human reading the input."
        )
        citations = [item.id for item in evidence[:3]]

    # --- facts -------------------------------------------------------------
    facts = []
    for shape, count in top_shapes[:3]:
        ids = ids_for_shape.get(shape, [])[:6]
        facts.append({
            "statement": f'The pattern "{shape[:100]}" appears {count} time(s) in the input.',
            "evidence": ids,
        })
    if deploy_items:
        facts.append({
            "statement": "Deployment notes were supplied alongside the failure evidence.",
            "evidence": [item.id for item in deploy_items[:3]],
        })

    # --- hypotheses --------------------------------------------------------
    # Mechanical, and labelled as such. Each one is really "this cluster is the
    # cause", which is a starting point rather than an explanation.
    hypotheses = []
    for index, (shape, count) in enumerate(top_shapes):
        ids = ids_for_shape.get(shape, [])
        share = count / max(1, len(errors))
        hypotheses.append({
            "title": f"The failure is centred on: {shape[:90]}",
            "explanation": (
                f"This message pattern accounts for {share:.0%} of the error-level "
                f"evidence ({count} of {len(errors)} items). The offline engine ranks "
                "clusters by frequency; it does not know what this message means or "
                "what could produce it."
            ),
            # Frequency share is a weak signal, so the ceiling is deliberately
            # low. A number above 0.5 here would be an unearned claim.
            "confidence": round(min(0.45, 0.15 + share * 0.3), 2),
            "supporting_evidence": ids[:6],
            "contradicting_evidence": [],
            "recommended_test": (
                "Read these lines in full and identify the component that emits them, "
                "then check whether the same message appears before the incident window."
            ),
        })
        if index + 1 >= hypothesis_count:
            break

    if deploy_items and len(hypotheses) < hypothesis_count:
        hypotheses.append({
            "title": "A recent deployment changed behaviour",
            "explanation": (
                "Deployment notes were supplied. This hypothesis is listed because it is "
                "the standard suspect, NOT because any evidence connects the deployment "
                "to the failures - the offline engine cannot make that connection."
            ),
            "confidence": 0.2,
            "supporting_evidence": [item.id for item in deploy_items[:3]],
            "contradicting_evidence": [],
            "recommended_test": (
                "Check whether these errors exist in logs from before the deployment."
            ),
        })

    # --- next actions ------------------------------------------------------
    next_actions = []
    if errors:
        next_actions.append({
            "action": f"Read the {min(5, len(errors))} earliest error lines in full context.",
            "rationale": "The first failure usually carries more information than the retries after it.",
            "priority": "P1",
            "owner_role": "engineer",
            "evidence": [item.id for item in errors[:5]],
        })
    if deploy_items:
        next_actions.append({
            "action": "Compare error rates from before and after the deployment window.",
            "rationale": "Establishes whether the deployment is correlated at all, before assuming it is causal.",
            "priority": "P2",
            "owner_role": "sre",
            "evidence": [item.id for item in deploy_items[:2]],
        })
    next_actions.append({
        "action": "Configure an API key in .env and re-run the analysis.",
        "rationale": (
            "Causal reasoning, disconfirming evidence and the reasoning-risk audit "
            "require a language model. This run produced none of them."
        ),
        "priority": "P2",
        "owner_role": "engineer",
        "evidence": [],
    })

    return {
        "summary": {"text": summary_text, "citations": citations},
        "audiences": {},
        "inferred_timeline": [],
        "facts": facts,
        "assumptions": [{
            "statement": "The clusters above correspond to distinct failures rather than one failure reported repeatedly.",
            "why": "Messages were grouped by text shape only, with no knowledge of the systems involved.",
            "how_to_verify": "Check whether the grouped lines share a request id or a trace id.",
        }],
        "hypotheses": hypotheses,
        "reasoning_risks": [],
        "next_actions": next_actions,
        "open_questions": [
            {
                "question": "What does the dominant error message actually mean in this system?",
                "why_it_matters": "Frequency ranking is not explanation. Without this, the ranking above is just counting.",
            },
            {
                "question": "Was there a change - deploy, config, traffic, dependency - in the hour before the first error?",
                "why_it_matters": "The offline engine cannot correlate across sources.",
            },
        ],
    }
