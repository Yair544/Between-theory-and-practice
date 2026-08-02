"""
The analysis pipeline.

Order matters and is fixed:

    redact -> extract evidence -> observed timeline -> model pass
           -> verify -> strip invalid citations -> challenge pass
           -> rule-based bias detection -> assemble -> render report

Redaction is first so nothing sensitive can reach a provider. Evidence
extraction is second so IDs exist before the model does anything. Verification
runs before the challenge pass so the devil's advocate argues against a
hypothesis whose citations have already been cleaned, and the rule-based
detectors run last because several of them need the verification result.

A failure in the model pass degrades to the offline engine rather than returning
an error page: a partial analysis the user can see is more useful than a stack
trace, as long as it is honestly labelled.
"""

from __future__ import annotations

import time
import uuid

from ..config import Settings
from ..models import (
    Analysis, AnalysisMeta, Assumption, BiasCatalogEntry, Fact, Hypothesis,
    IncidentRequest, NextAction, OpenQuestion, Summary, TimelineEvent,
)
from . import biases, offline_engine, prompts, report, risk_detector, timeline as timeline_svc
from .evidence import evidence_ids, extract_evidence, render_for_prompt
from .llm import LLMError, build_client, parse_json_object
from .redaction import redact_mapping
from .verifier import strip_invalid_citations, verify


def _coverage_note(evidence, coverage: dict) -> str:
    """A line for the prompt describing how complete the input is."""
    total = coverage["total_items"]
    timed = coverage["timed_items"]
    if total == 0:
        return "No evidence items were extracted."
    return (
        f"{total} evidence items; {timed} carry a parseable timestamp and "
        f"{total - timed} do not. Sources present: "
        f"{', '.join(sorted({item.source for item in evidence}))}. "
        "Treat the untimed items as unordered - do not assume their position."
    )


def _render_observed(events: list[TimelineEvent]) -> str:
    return "\n".join(
        f"- {event.timestamp or 'unknown'}: {event.label} "
        f"[{', '.join(event.evidence)}]"
        for event in events[:60]
    )


def _run_model_pass(client, *, request, evidence, observed, coverage_note, settings):
    """One structured analysis call. Returns (payload, warnings)."""
    user_prompt = prompts.build_analysis_prompt(
        title=request.title,
        evidence_block=render_for_prompt(evidence),
        observed_timeline=_render_observed(observed),
        hypothesis_count=request.options.hypothesis_count,
        coverage_note=coverage_note,
    )

    result = client.complete(
        system=prompts.ANALYSIS_SYSTEM,
        user=user_prompt,
        max_tokens=settings.max_output_tokens,
        json_schema=prompts.ANALYSIS_SCHEMA,
    )
    payload, parse_warnings = parse_json_object(result.text)
    return payload, [*result.warnings, *parse_warnings], result


def _run_challenge_pass(client, *, leader, evidence, settings) -> str:
    """
    Ask a fresh context to argue against the leading hypothesis.

    Failures here are swallowed: the rebuttal is a bonus, and losing it should
    not cost the user the analysis they already have.
    """
    try:
        result = client.complete(
            system=prompts.CHALLENGE_SYSTEM,
            user=prompts.build_challenge_prompt(
                hypothesis_title=leader.get("title", ""),
                hypothesis_explanation=leader.get("explanation", ""),
                supporting=list(leader.get("supporting_evidence") or []),
                contradicting=list(leader.get("contradicting_evidence") or []),
                evidence_block=render_for_prompt(evidence),
            ),
            max_tokens=2000,
            json_schema=prompts.CHALLENGE_SCHEMA,
        )
        payload, _ = parse_json_object(result.text)
        return str(payload.get("rebuttal") or "")
    except Exception:  # noqa: BLE001 - a missing rebuttal must not cost the analysis
        return ""


def _merge_timeline(observed: list[TimelineEvent], inferred: list[dict]) -> list[TimelineEvent]:
    """Observed events plus whatever the model deduced, in time order."""
    events = list(observed)
    for index, raw in enumerate(inferred, start=1):
        stamp = (raw.get("timestamp") or "").strip()
        events.append(TimelineEvent(
            id=f"TI{index}",
            timestamp=stamp or None,
            label=raw.get("label", ""),
            detail=raw.get("detail", ""),
            evidence=list(raw.get("evidence") or []),
            inferred=True,
        ))
    # Events with no timestamp sort last; they cannot be placed.
    return sorted(events, key=lambda event: (event.timestamp is None, event.timestamp or ""))


def run_analysis(request: IncidentRequest, settings: Settings) -> Analysis:
    started = time.perf_counter()
    warnings: list[str] = []

    # 1. redact ------------------------------------------------------------
    sources = request.sources()
    redacted_count = 0
    if request.options.redact_pii and settings.redact_pii:
        sources, redacted_count = redact_mapping(sources)
    elif not request.options.redact_pii:
        warnings.append(
            "Redaction was disabled for this run. Raw input, including anything "
            "personal in it, was sent to the model provider."
        )

    # 2. evidence ----------------------------------------------------------
    evidence, stats = extract_evidence(
        sources, max_chars=settings.max_input_chars, redacted_count=redacted_count
    )
    if stats.truncated:
        warnings.append(
            "The input exceeded MAX_INPUT_CHARS and was truncated per source. "
            "Evidence after the cut-off is not in this analysis."
        )
    known_ids = evidence_ids(evidence)

    # 3. observed timeline -------------------------------------------------
    observed = timeline_svc.build_timeline(evidence)
    coverage = timeline_svc.coverage(evidence)

    # 4. model pass (or the offline engine) --------------------------------
    offline = settings.offline
    provider = settings.provider
    model_name = settings.active_model

    if offline:
        payload = offline_engine.analyse(
            evidence, title=request.title, hypothesis_count=request.options.hypothesis_count
        )
    else:
        client = build_client(settings)
        try:
            payload, model_warnings, result = _run_model_pass(
                client,
                request=request,
                evidence=evidence,
                observed=observed,
                coverage_note=_coverage_note(evidence, coverage),
                settings=settings,
            )
            warnings.extend(model_warnings)
            model_name = result.model
        except LLMError as exc:
            # Degrade rather than fail. The banner in the UI will say offline.
            warnings.append(f"The model call failed ({exc}). Fell back to the offline engine.")
            offline = True
            provider = "offline"
            model_name = "deterministic-engine"
            payload = offline_engine.analyse(
                evidence, title=request.title, hypothesis_count=request.options.hypothesis_count
            )

    # 5. verify, then remove fabricated ids from what the UI will render ----
    verification = verify(payload, known_ids)
    stripped = strip_invalid_citations(payload, known_ids)
    if stripped:
        warnings.append(
            f"{stripped} citation(s) pointed at evidence that does not exist and were "
            "removed from the displayed claims. They are listed in the verification report."
        )

    # 6. devil's advocate --------------------------------------------------
    raw_hypotheses = list(payload.get("hypotheses") or [])
    raw_hypotheses.sort(key=lambda item: item.get("confidence", 0), reverse=True)

    if request.options.devils_advocate and not offline and raw_hypotheses:
        rebuttal = _run_challenge_pass(
            build_client(settings), leader=raw_hypotheses[0], evidence=evidence, settings=settings
        )
        if rebuttal:
            raw_hypotheses[0]["rebuttal"] = rebuttal
        else:
            warnings.append("The counter-argument pass did not return a usable result.")

    # 7. reasoning risks ---------------------------------------------------
    heuristic_risks = risk_detector.detect(
        hypotheses=raw_hypotheses,
        evidence=evidence,
        summary_text=(payload.get("summary") or {}).get("text", ""),
        verification_failed=bool(verification.unsupported or verification.invalid_citations),
        offline=offline,
    )
    risks = risk_detector.merge(list(payload.get("reasoning_risks") or []), heuristic_risks)

    # 8. assemble ----------------------------------------------------------
    summary_raw = payload.get("summary") or {}
    analysis = Analysis(
        id=uuid.uuid4().hex[:12],
        title=request.title or "Untitled incident",
        meta=AnalysisMeta(
            provider=provider,
            model=model_name,
            offline=offline,
            duration_ms=int((time.perf_counter() - started) * 1000),
            warnings=warnings,
            input_stats=stats,
        ),
        evidence=evidence,
        summary=Summary(
            text=summary_raw.get("text", ""),
            citations=list(summary_raw.get("citations") or []),
            audiences={k: v for k, v in (payload.get("audiences") or {}).items() if v},
        ),
        timeline=_merge_timeline(observed, list(payload.get("inferred_timeline") or [])),
        facts=[
            Fact(id=f"F{i}", statement=item.get("statement", ""),
                 evidence=list(item.get("evidence") or []))
            for i, item in enumerate(payload.get("facts") or [], start=1)
        ],
        assumptions=[
            Assumption(id=f"A{i}", statement=item.get("statement", ""),
                       why=item.get("why", ""), how_to_verify=item.get("how_to_verify", ""))
            for i, item in enumerate(payload.get("assumptions") or [], start=1)
        ],
        hypotheses=[
            Hypothesis(
                id=f"H{i}",
                title=item.get("title", ""),
                explanation=item.get("explanation", ""),
                confidence=max(0.0, min(1.0, float(item.get("confidence") or 0))),
                supporting_evidence=list(item.get("supporting_evidence") or []),
                contradicting_evidence=list(item.get("contradicting_evidence") or []),
                recommended_test=item.get("recommended_test", ""),
                rebuttal=item.get("rebuttal", ""),
            )
            for i, item in enumerate(raw_hypotheses, start=1)
        ],
        next_actions=[
            NextAction(
                id=f"N{i}",
                action=item.get("action", ""),
                rationale=item.get("rationale", ""),
                priority=item.get("priority", "P3"),
                owner_role=item.get("owner_role", "engineer"),
                evidence=list(item.get("evidence") or []),
            )
            for i, item in enumerate(payload.get("next_actions") or [], start=1)
        ],
        open_questions=[
            OpenQuestion(id=f"Q{i}", question=item.get("question", ""),
                         why_it_matters=item.get("why_it_matters", ""))
            for i, item in enumerate(payload.get("open_questions") or [], start=1)
        ],
        reasoning_risks=risks,
        bias_catalog=[BiasCatalogEntry(**entry) for entry in biases.catalog_for_api()],
        verification=verification,
    )

    analysis.report_markdown = report.build_markdown(analysis)
    return analysis
