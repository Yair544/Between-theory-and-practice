"""
HTTP routes.

Thin on purpose: parse, delegate, serialise. Anything resembling analysis logic
belongs in backend/services.
"""

from __future__ import annotations

import logging
from collections import OrderedDict

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from ..config import settings
from ..models import Analysis, IncidentRequest, SampleSummary
from ..services import analyzer, biases, samples
from ..services.llm import LLMError

logger = logging.getLogger("incidentiq")
router = APIRouter(prefix="/api")

# Recent analyses, kept only so the Markdown export can be fetched by id.
# In-memory and bounded: this is a single-user local tool, and persisting
# incident data to disk without being asked would be the wrong default for
# something that ingests production logs.
_RECENT: OrderedDict[str, Analysis] = OrderedDict()
_RECENT_LIMIT = 20


def _remember(analysis: Analysis) -> None:
    _RECENT[analysis.id] = analysis
    while len(_RECENT) > _RECENT_LIMIT:
        _RECENT.popitem(last=False)


@router.get("/health")
def health() -> dict:
    """Configuration snapshot. Never includes a key, only whether one is set."""
    return {"status": "ok", **settings.describe()}


@router.get("/biases")
def bias_catalog() -> list[dict]:
    """The catalogue the analysis audits against."""
    return biases.catalog_for_api()


@router.get("/samples", response_model=list[SampleSummary])
def list_samples() -> list[SampleSummary]:
    return samples.list_samples()


@router.get("/samples/{sample_id}")
def get_sample(sample_id: str) -> dict:
    sample = samples.get_sample(sample_id)
    if sample is None:
        raise HTTPException(status_code=404, detail=f"No sample incident named '{sample_id}'.")
    return sample


@router.post("/analyze", response_model=Analysis)
def analyze(request: IncidentRequest) -> Analysis:
    if request.is_empty():
        raise HTTPException(
            status_code=400,
            detail=(
                "Not enough input to analyse. Provide at least one field with 10 or more "
                "characters — a description, or a few log lines."
            ),
        )

    try:
        analysis = analyzer.run_analysis(request, settings)
    except LLMError as exc:
        # The analyser normally degrades to the offline engine, so reaching here
        # means the failure happened outside the model pass.
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Analysis failed")
        raise HTTPException(
            status_code=500,
            detail=f"The analysis pipeline failed: {exc}",
        ) from exc

    _remember(analysis)
    return analysis


@router.get("/analysis/{analysis_id}/report.md", response_class=PlainTextResponse)
def get_report(analysis_id: str) -> str:
    analysis = _RECENT.get(analysis_id)
    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="That analysis is no longer in memory. Re-run it, or use the "
                   "Download button in the Postmortem tab.",
        )
    return analysis.report_markdown
