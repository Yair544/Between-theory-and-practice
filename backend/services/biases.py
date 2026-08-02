"""
The bias and fallacy catalogue.

These eight entries are taken verbatim from the table in the project brief.
They are defined once here and used in three places — the prompt sent to the
model, the deterministic detectors, and the reference table in the UI — so the
tool cannot end up checking for one set of biases and reporting on another.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BiasDefinition:
    id: str
    name: str
    appears_as: str        # wording from the brief
    detector_note: str     # what our heuristics can and cannot see


CATALOG: tuple[BiasDefinition, ...] = (
    BiasDefinition(
        id="confirmation_bias",
        name="Confirmation bias",
        appears_as="Focusing only on evidence that supports the first suspected root cause.",
        detector_note=(
            "Detectable in structure: a hypothesis with supporting evidence and an "
            "empty contradicting list means nobody went looking for a counter-example."
        ),
    ),
    BiasDefinition(
        id="anchoring_bias",
        name="Anchoring bias",
        appears_as="Allowing the first error message or AI answer to dominate the investigation.",
        detector_note=(
            "Detectable in structure: the leading hypothesis citing only the earliest "
            "evidence items means the investigation never moved past its first impression."
        ),
    ),
    BiasDefinition(
        id="automation_bias",
        name="Automation bias",
        appears_as="Trusting AI-generated conclusions because they sound professional.",
        detector_note=(
            "Not detectable from the output alone — this bias lives in the reader, not "
            "the text. Raised whenever a hypothesis is presented with high confidence "
            "and thin evidence, because that is the shape that invites it."
        ),
    ),
    BiasDefinition(
        id="post_hoc",
        name="Post hoc fallacy",
        appears_as=(
            "Assuming that because a deployment happened before the incident, "
            "it must have caused the incident."
        ),
        detector_note=(
            "Detectable in structure: a hypothesis blaming a deployment whose only "
            "support is that the deployment came first."
        ),
    ),
    BiasDefinition(
        id="availability_bias",
        name="Availability bias",
        appears_as="Preferring explanations that resemble bugs you have personally seen before.",
        detector_note=(
            "Partly detectable: hypotheses reaching for stock causes (memory leak, DNS, "
            "cache) with no evidence in this incident naming them."
        ),
    ),
    BiasDefinition(
        id="overconfidence_bias",
        name="Overconfidence bias",
        appears_as="Presenting a hypothesis as certain even when evidence is incomplete.",
        detector_note=(
            "Detectable numerically: high stated confidence against a small number of "
            "citations, or certainty language in the summary."
        ),
    ),
    BiasDefinition(
        id="hindsight_bias",
        name="Hindsight bias",
        appears_as="After finding a likely cause, claiming it was obvious from the beginning.",
        detector_note=(
            "Detectable by wording: 'obviously', 'clearly', 'as expected' applied to a "
            "cause that was not known when the incident started."
        ),
    ),
    BiasDefinition(
        id="base_rate_neglect",
        name="Base-rate neglect",
        appears_as="Overemphasizing rare errors while ignoring common causes of production failures.",
        detector_note=(
            "Detectable in structure: the leading hypothesis resting on an evidence item "
            "that appears once, while a pattern repeated dozens of times is unexplained."
        ),
    ),
)

BY_ID: dict[str, BiasDefinition] = {entry.id: entry for entry in CATALOG}


def catalog_for_prompt() -> str:
    """The catalogue as the model sees it."""
    return "\n".join(
        f"- {entry.id}: {entry.name} — {entry.appears_as}" for entry in CATALOG
    )


def catalog_for_api() -> list[dict]:
    """The catalogue as the UI sees it."""
    return [
        {"id": entry.id, "name": entry.name, "appears_as": entry.appears_as}
        for entry in CATALOG
    ]


def name_of(bias_id: str) -> str:
    entry = BY_ID.get(bias_id)
    return entry.name if entry else bias_id.replace("_", " ").title()
