"""
The prompt library.

Every instruction sent to a model lives in this file. Keeping them together (a)
makes them reviewable as a unit, (b) lets docs/PROMPTS.md quote line numbers
instead of paraphrasing, and (c) means a prompt change is a visible diff rather
than a string edited somewhere in the middle of the analyser.

Three prompts are used:
  1. ANALYSIS   - the main pass. Produces the structured investigation.
  2. CHALLENGE  - the devil's advocate. Given the leading hypothesis, it is told
                  to argue against it. Run as a separate call with a fresh
                  context so the model is not merely continuing its own train
                  of thought and agreeing with itself.
  3. AUDIENCE   - included in the analysis schema rather than as a third call,
                  because rewriting for three audiences from the same structured
                  facts is cheap and keeps the claims identical across versions.
"""

from __future__ import annotations

from .biases import catalog_for_prompt

# ---------------------------------------------------------------- system ----

ANALYSIS_SYSTEM = """\
You are IncidentIQ, an assistant that helps software engineers investigate a \
production incident. You are not an oracle. Your job is to organise evidence and \
generate testable explanations, not to announce the answer.

Absolute rules:

1. EVIDENCE IDS. The user message contains numbered evidence items in the form \
[E1], [E2], .... Every claim you make must cite the IDs it rests on. Never cite \
an ID that does not appear in the input. If you cannot support a statement with \
an ID, either drop it or move it into `assumptions`, where unproven statements \
belong.

2. FOUR SEPARATE KINDS OF STATEMENT. Keep them apart:
   - facts: directly supported by the evidence. Must cite IDs.
   - assumptions: believed but not proven. Must say how they could be checked.
   - hypotheses: possible explanations that require testing.
   - next_actions: things a human should do next.
   Do not promote a hypothesis into a fact because it feels likely.

3. NEVER CLAIM A ROOT CAUSE. Produce several competing explanations, including at \
least one that does not involve the most recent deployment. If one explanation \
dominates, still supply a genuine alternative rather than a strawman.

4. LOOK FOR DISCONFIRMING EVIDENCE. For every hypothesis, actively search the \
input for evidence that argues against it, and list it in \
`contradicting_evidence`. An empty contradicting list is a claim that you looked \
and found nothing - do not use it as a default.

5. CONFIDENCE IS EVIDENTIAL, NOT RHETORICAL. `confidence` is how much of the \
evidence the explanation accounts for, on a 0-1 scale. Do not exceed 0.75 unless \
multiple independent evidence items point the same way and none contradict. \
Correlation in time is not causation: a deployment preceding an incident is a \
lead, not a cause.

6. AUDIT YOUR OWN REASONING. Review the analysis you just produced against the \
listed biases and report the ones that genuinely apply, with the specific place \
they appear. Do not report a bias you cannot point at. Reporting none is \
acceptable and preferable to inventing one.

7. NO FABRICATION. If the evidence is too thin to answer something, say so in \
`open_questions`. A short honest analysis is worth more than a complete-looking \
one built on invention.

Write in plain professional English. No marketing tone, no emoji, no hedging \
phrases that carry no information ("it is possible that there may be").
"""

CHALLENGE_SYSTEM = """\
You are a skeptical senior engineer reviewing someone else's incident analysis. \
You did not write it and you have no stake in it being right.

Your only task is to argue that the leading hypothesis is WRONG. Specifically:
  - name the evidence it fails to explain
  - name the evidence that actively contradicts it
  - name the alternative explanation that fits the same evidence
  - name the single cheapest observation that would falsify it

Cite evidence IDs. Do not soften the critique to be polite, and do not invent \
evidence to strengthen it. If, after genuinely trying, you cannot construct a \
serious case against the hypothesis, say exactly that and explain what makes it \
hard to argue with - that is a real finding, not a failure.
"""

# ------------------------------------------------------------ user prompts --


def build_analysis_prompt(
    *,
    title: str,
    evidence_block: str,
    observed_timeline: str,
    hypothesis_count: int,
    coverage_note: str,
) -> str:
    """The user turn for the main analysis pass."""
    return f"""\
# Incident
{title or "(untitled)"}

# Evidence
Each item below is one line of input, already numbered. These IDs are the only \
ones that exist; citing anything else is an error.

{evidence_block}

# Observed timeline (built deterministically from the timestamps above)
{observed_timeline or "(no parseable timestamps were found)"}

# Coverage
{coverage_note}

# Biases and fallacies to audit against
{catalog_for_prompt()}

# What to produce
Return a single JSON object matching the required schema.

Specific requirements for this run:
- Produce exactly {hypothesis_count} hypotheses, ordered by descending confidence.
- At least one hypothesis must NOT blame the most recent deployment or config change.
- `inferred_timeline` holds only events you deduced that are NOT already in the \
observed timeline above. Leave it empty if you have nothing to add - repeating \
observed events there would misrepresent them as inferences.
- `audiences` rewrites the same summary for three readers. The wording changes; \
the claims do not. The manager version must not add certainty the engineer \
version does not have.
- `reasoning_risks[].bias` must be one of the catalogue ids listed above.
"""


def build_challenge_prompt(
    *,
    hypothesis_title: str,
    hypothesis_explanation: str,
    supporting: list[str],
    contradicting: list[str],
    evidence_block: str,
) -> str:
    """The user turn for the devil's-advocate pass."""
    return f"""\
# The hypothesis under review
{hypothesis_title}

{hypothesis_explanation}

Claimed supporting evidence: {", ".join(supporting) or "none"}
Claimed contradicting evidence: {", ".join(contradicting) or "none"}

# The full evidence set
{evidence_block}

# What to produce
A single JSON object with one field, "rebuttal": a paragraph of at most 120 words \
arguing against the hypothesis, citing evidence IDs.
"""


# ---------------------------------------------------------------- schemas ---

# Hand-written rather than generated from the Pydantic models. The model's
# output is a subset of the analysis document (it never produces the evidence
# list - that is ours), and structured outputs reject several constraints that
# Pydantic emits by default.

_STRING_ARRAY = {"type": "array", "items": {"type": "string"}}

ANALYSIS_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "summary", "audiences", "inferred_timeline", "facts", "assumptions",
        "hypotheses", "reasoning_risks", "next_actions", "open_questions",
    ],
    "properties": {
        "summary": {
            "type": "object",
            "additionalProperties": False,
            "required": ["text", "citations"],
            "properties": {
                "text": {
                    "type": "string",
                    "description": "3-6 sentences: what failed, when, who is affected, what is still unknown.",
                },
                "citations": _STRING_ARRAY,
            },
        },
        "audiences": {
            "type": "object",
            "additionalProperties": False,
            "required": ["engineer", "manager", "support"],
            "properties": {
                "engineer": {"type": "string", "description": "Technical, specific, names systems."},
                "manager": {"type": "string", "description": "Impact and uncertainty. No jargon, no added certainty."},
                "support": {"type": "string", "description": "What to tell an affected user right now."},
            },
        },
        "inferred_timeline": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["timestamp", "label", "detail", "evidence"],
                "properties": {
                    "timestamp": {"type": "string", "description": "ISO-8601, or empty string if unknown."},
                    "label": {"type": "string"},
                    "detail": {"type": "string"},
                    "evidence": _STRING_ARRAY,
                },
            },
        },
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["statement", "evidence"],
                "properties": {
                    "statement": {"type": "string"},
                    "evidence": _STRING_ARRAY,
                },
            },
        },
        "assumptions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["statement", "why", "how_to_verify"],
                "properties": {
                    "statement": {"type": "string"},
                    "why": {"type": "string"},
                    "how_to_verify": {"type": "string"},
                },
            },
        },
        "hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "title", "explanation", "confidence",
                    "supporting_evidence", "contradicting_evidence", "recommended_test",
                ],
                "properties": {
                    "title": {"type": "string", "description": "One line, mechanism-first."},
                    "explanation": {"type": "string"},
                    "confidence": {"type": "number", "description": "0-1. See rule 5."},
                    "supporting_evidence": _STRING_ARRAY,
                    "contradicting_evidence": _STRING_ARRAY,
                    "recommended_test": {
                        "type": "string",
                        "description": "One concrete observation that would confirm or kill it.",
                    },
                },
            },
        },
        "reasoning_risks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["bias", "where", "impact", "mitigation", "severity"],
                "properties": {
                    "bias": {"type": "string", "description": "A catalogue id from the prompt."},
                    "where": {"type": "string", "description": "The specific place it appears."},
                    "impact": {"type": "string"},
                    "mitigation": {"type": "string"},
                    "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
                },
            },
        },
        "next_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["action", "rationale", "priority", "owner_role", "evidence"],
                "properties": {
                    "action": {"type": "string"},
                    "rationale": {"type": "string"},
                    "priority": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]},
                    "owner_role": {
                        "type": "string",
                        "enum": ["engineer", "sre", "manager", "support", "security"],
                    },
                    "evidence": _STRING_ARRAY,
                },
            },
        },
        "open_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["question", "why_it_matters"],
                "properties": {
                    "question": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                },
            },
        },
    },
}

CHALLENGE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["rebuttal"],
    "properties": {"rebuttal": {"type": "string"}},
}
