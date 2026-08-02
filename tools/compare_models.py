#!/usr/bin/env python3
"""
Run one incident through two providers and compare the conclusions.

    python tools/compare_models.py checkout-v241

Requires both ANTHROPIC_API_KEY and OPENAI_API_KEY in .env.

Why this exists: the brief asks for "comparing multiple prompts or models", and
a second independent model is the cheapest way to separate "this is what the
evidence supports" from "this is what that model believes". When two models read
identical evidence with an identical prompt and disagree about the root cause,
the disagreement is the finding — and neither answer should be trusted until the
recommended test has been run.

Note what this does NOT show. Agreement between two models is weaker evidence
than it feels: they share training data, and they are both reading the same
prompt, so the same framing biases both.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.config import load_settings  # noqa: E402
from backend.models import IncidentRequest  # noqa: E402
from backend.services import analyzer, samples  # noqa: E402

LINE = "=" * 72


def request_for(sample_id: str) -> IncidentRequest:
    sample = samples.get_sample(sample_id)
    if sample is None:
        available = ", ".join(s.id for s in samples.list_samples())
        raise SystemExit(f"No sample '{sample_id}'. Available: {available}")
    return IncidentRequest(
        title=sample.get("title", ""),
        description=sample.get("description", ""),
        logs=sample.get("logs", ""),
        errors=sample.get("errors", ""),
        alerts=sample.get("alerts", ""),
        deploy_notes=sample.get("deploy_notes", ""),
        user_reports=sample.get("user_reports", ""),
    )


def summarise(label: str, analysis) -> dict:
    leader = analysis.hypotheses[0] if analysis.hypotheses else None
    return {
        "label": label,
        "model": analysis.meta.model,
        "offline": analysis.meta.offline,
        "duration_ms": analysis.meta.duration_ms,
        "leader": leader.title if leader else "(none)",
        "confidence": leader.confidence if leader else 0.0,
        "citations": set(leader.supporting_evidence) if leader else set(),
        "grounding": analysis.verification.grounding_score,
        "invalid": len(analysis.verification.invalid_citations),
        "risks": [risk.bias for risk in analysis.reasoning_risks],
    }


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python tools/compare_models.py <sample-id>")

    request = request_for(sys.argv[1])
    base = load_settings()

    if not (base.anthropic_api_key and base.openai_api_key):
        raise SystemExit(
            "Both ANTHROPIC_API_KEY and OPENAI_API_KEY must be set in .env for a "
            "cross-model comparison."
        )

    results = []
    for provider in ("anthropic", "openai"):
        settings = replace(base, provider=provider)
        print(f"Running {provider}…", flush=True)
        results.append(summarise(provider, analyzer.run_analysis(request, settings)))

    a, b = results

    print()
    print(LINE)
    print(f" Same evidence, same prompt, two models — {sys.argv[1]}")
    print(LINE)
    for row in results:
        print(f"\n [{row['label']}]  {row['model']}  ({row['duration_ms']} ms)")
        print(f"   leading hypothesis : {row['leader']}")
        print(f"   confidence         : {row['confidence']:.0%}")
        print(f"   cites              : {', '.join(sorted(row['citations'])) or '-'}")
        print(f"   grounding          : {row['grounding']:.0%}"
              f"  ({row['invalid']} invented citation(s))")
        print(f"   risks flagged      : {', '.join(row['risks']) or 'none'}")

    shared = a["citations"] & b["citations"]
    union = a["citations"] | b["citations"]
    overlap = len(shared) / len(union) if union else 0.0

    print()
    print(LINE)
    print(f" Evidence overlap on the leading hypothesis : {overlap:.0%}")
    print(f" Confidence gap                             : "
          f"{abs(a['confidence'] - b['confidence']):.0%}")
    print()
    if overlap < 0.34:
        print(" The two models built their leading hypothesis from largely different")
        print(" evidence. Read both before accepting either.")
    else:
        print(" Both models leaned on much of the same evidence. That is agreement about")
        print(" what is salient, which is not the same as agreement about what is true.")
    print(LINE)


if __name__ == "__main__":
    main()
