"""Request-side schemas: what the browser sends us."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AnalysisOptions(BaseModel):
    """Per-run switches, all defaulting to the safer behaviour."""

    devils_advocate: bool = Field(
        default=True,
        description="Run a second pass that argues against the leading hypothesis.",
    )
    redact_pii: bool = Field(
        default=True,
        description="Replace emails, IPs, tokens and card numbers before calling a provider.",
    )
    hypothesis_count: int = Field(default=4, ge=2, le=8)
    language: Literal["en", "he"] = Field(
        default="en",
        description=(
            "Language for the model's prose. Evidence text is never translated - "
            "a log line quoted back in another language is no longer a quotation."
        ),
    )


class IncidentRequest(BaseModel):
    """
    The raw evidence bundle.

    Every field is a free-text blob and every one is optional; real incidents
    arrive incomplete, and refusing to analyse until all six are filled in would
    make the tool useless exactly when it is needed.
    """

    title: str = ""
    description: str = ""
    logs: str = ""
    errors: str = ""
    alerts: str = ""
    deploy_notes: str = ""
    user_reports: str = ""
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)

    def sources(self) -> dict[str, str]:
        """Map of source key -> text, skipping the blanks."""
        candidates = {
            "description": self.description,
            "logs": self.logs,
            "errors": self.errors,
            "alerts": self.alerts,
            "deploy_notes": self.deploy_notes,
            "user_reports": self.user_reports,
        }
        return {key: value for key, value in candidates.items() if value and value.strip()}

    def is_empty(self) -> bool:
        return not any(len(v.strip()) >= 10 for v in self.sources().values())


class SampleSummary(BaseModel):
    """Metadata for one bundled example incident, used by the sidebar."""

    id: str
    title: str
    scenario: str = ""
    description: str = ""
