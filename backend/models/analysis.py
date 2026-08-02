"""
Response-side schemas: the analysis document.

The shape encodes the discipline the brief asks for. Facts, assumptions,
hypotheses and actions are four distinct types rather than one "findings" list,
so it is structurally impossible for the engine to return a guess in the place
where a fact belongs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["critical", "high", "medium", "low", "info"]
Priority = Literal["P1", "P2", "P3", "P4"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Evidence(BaseModel):
    """One atomic, citable piece of input. Everything else references these."""

    id: str                       # "E1", "E2", ... stable within one analysis
    source: str                   # logs | errors | alerts | deploy_notes | ...
    text: str                     # the raw line, after redaction
    line: int | None = None       # 1-based position within its source blob
    timestamp: str | None = None  # ISO-8601 if one could be parsed
    severity: Severity | None = None


class TimelineEvent(BaseModel):
    id: str
    timestamp: str | None = None
    label: str
    detail: str = ""
    evidence: list[str] = Field(default_factory=list)
    inferred: bool = False   # True = deduced, not read from a timestamped line


class Fact(BaseModel):
    """A statement the input supports directly. Must cite evidence."""

    id: str
    statement: str
    evidence: list[str] = Field(default_factory=list)


class Assumption(BaseModel):
    """Believed but unproven. Carries its own falsification route."""

    id: str
    statement: str
    why: str = ""
    how_to_verify: str = ""


class Hypothesis(BaseModel):
    id: str
    title: str
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    recommended_test: str = ""
    rebuttal: str = ""   # filled by the devil's-advocate pass


class ReasoningRisk(BaseModel):
    """A cognitive bias or logical fallacy detected in *our* reasoning."""

    id: str
    bias: str            # catalogue id, e.g. "post_hoc"
    name: str            # human-readable name from the brief
    where: str
    impact: str = ""
    mitigation: str = ""
    severity: Severity = "medium"
    detected_by: Literal["heuristic", "model", "both"] = "model"
    evidence: list[str] = Field(default_factory=list)


class NextAction(BaseModel):
    id: str
    action: str
    rationale: str = ""
    priority: Priority = "P3"
    owner_role: str = "engineer"
    evidence: list[str] = Field(default_factory=list)


class OpenQuestion(BaseModel):
    id: str
    question: str
    why_it_matters: str = ""


class UnsupportedClaim(BaseModel):
    """A model statement that cited nothing."""

    statement: str
    where: str


class InvalidCitation(BaseModel):
    """A model statement that cited an evidence id which does not exist."""

    citation: str
    where: str


class Verification(BaseModel):
    """
    Output of the grounding check.

    grounding_score is the share of citable claims that carry at least one valid
    citation. It measures traceability, not correctness: a claim can cite real
    evidence and still be wrong about what that evidence means.
    """

    claims_checked: int = 0
    unsupported: list[UnsupportedClaim] = Field(default_factory=list)
    invalid_citations: list[InvalidCitation] = Field(default_factory=list)
    grounding_score: float = 1.0


class BiasCatalogEntry(BaseModel):
    id: str
    name: str
    appears_as: str


class InputStats(BaseModel):
    total_chars: int = 0
    truncated: bool = False
    redacted_count: int = 0
    sources: list[str] = Field(default_factory=list)


class AnalysisMeta(BaseModel):
    provider: str
    model: str
    offline: bool
    duration_ms: int = 0
    created_at: str = Field(default_factory=_now)
    warnings: list[str] = Field(default_factory=list)
    input_stats: InputStats = Field(default_factory=InputStats)


class Summary(BaseModel):
    text: str = ""
    citations: list[str] = Field(default_factory=list)
    audiences: dict[str, str] = Field(default_factory=dict)


class Analysis(BaseModel):
    """The complete document returned by POST /api/analyze."""

    id: str
    title: str = ""
    meta: AnalysisMeta

    evidence: list[Evidence] = Field(default_factory=list)
    summary: Summary = Field(default_factory=Summary)
    timeline: list[TimelineEvent] = Field(default_factory=list)

    facts: list[Fact] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    next_actions: list[NextAction] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)

    reasoning_risks: list[ReasoningRisk] = Field(default_factory=list)
    bias_catalog: list[BiasCatalogEntry] = Field(default_factory=list)

    verification: Verification = Field(default_factory=Verification)
    report_markdown: str = ""
