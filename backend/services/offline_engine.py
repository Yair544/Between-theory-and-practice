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
from . import offline_strings
from .textutil import message_shape as _shape


def analyse(
    evidence: list[Evidence],
    *,
    title: str,
    hypothesis_count: int,
    language: str = "en",
) -> dict:
    """Produce a payload in the same shape the model would return."""
    S = offline_strings.get(language)
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
        summary_text = S["summary.errors"].format(
            errors=len(errors),
            sources=len({item.source for item in errors}),
            patterns=len(shapes),
            top=top_shapes[0][1],
        )
        if first_error and first_error.timestamp:
            summary_text += S["summary.earliest"].format(ts=first_error.timestamp)
        summary_text += S["summary.nomodel"]
        citations = [item.id for item in errors[:5]]
    else:
        summary_text = S["summary.noerrors"].format(total=len(evidence))
        citations = [item.id for item in evidence[:3]]

    # --- facts -------------------------------------------------------------
    facts = []
    for shape, count in top_shapes[:3]:
        ids = ids_for_shape.get(shape, [])[:6]
        facts.append({
            "statement": S["fact.pattern"].format(shape=shape[:100], count=count),
            "evidence": ids,
        })
    if deploy_items:
        facts.append({
            "statement": S["fact.deploy"],
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
            "title": S["hyp.cluster.title"].format(shape=shape[:90]),
            "explanation": S["hyp.cluster.body"].format(
                share=f"{share:.0%}", count=count, errors=len(errors)
            ),
            # Frequency share is a weak signal, so the ceiling is deliberately
            # low. A number above 0.5 here would be an unearned claim.
            "confidence": round(min(0.45, 0.15 + share * 0.3), 2),
            "supporting_evidence": ids[:6],
            "contradicting_evidence": [],
            "recommended_test": S["hyp.cluster.test"],
        })
        if index + 1 >= hypothesis_count:
            break

    if deploy_items and len(hypotheses) < hypothesis_count:
        hypotheses.append({
            "title": S["hyp.deploy.title"],
            "explanation": S["hyp.deploy.body"],
            "confidence": 0.2,
            "supporting_evidence": [item.id for item in deploy_items[:3]],
            "contradicting_evidence": [],
            "recommended_test": S["hyp.deploy.test"],
        })

    # --- next actions ------------------------------------------------------
    next_actions = []
    if errors:
        next_actions.append({
            "action": S["action.readfirst"].format(count=min(5, len(errors))),
            "rationale": S["action.readfirst.why"],
            "priority": "P1",
            "owner_role": "engineer",
            "evidence": [item.id for item in errors[:5]],
        })
    if deploy_items:
        next_actions.append({
            "action": S["action.compare"],
            "rationale": S["action.compare.why"],
            "priority": "P2",
            "owner_role": "sre",
            "evidence": [item.id for item in deploy_items[:2]],
        })
    next_actions.append({
        "action": S["action.addkey"],
        "rationale": S["action.addkey.why"],
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
            "statement": S["assume.clusters"],
            "why": S["assume.clusters.why"],
            "how_to_verify": S["assume.clusters.verify"],
        }],
        "hypotheses": hypotheses,
        "reasoning_risks": [],
        "next_actions": next_actions,
        "open_questions": [
            {"question": S["q.meaning"], "why_it_matters": S["q.meaning.why"]},
            {"question": S["q.change"], "why_it_matters": S["q.change.why"]},
        ],
    }
