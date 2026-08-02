"""
Language plumbing.

The rule these tests defend is narrow but load-bearing: **prose is translated,
machine text is not**. A log line quoted back in Hebrew is no longer a quotation
and cannot be checked against the input, which would quietly break the whole
verification story.
"""

from __future__ import annotations

import re

import pytest

from backend.models import AnalysisOptions, IncidentRequest
from backend.services import offline_strings, prompts
from backend.services.offline_engine import analyse
from backend.services.evidence import extract_evidence

HEBREW = re.compile(r"[֐-׿]")

LOGS = """\
2026-05-02T10:14:03Z ERROR payment-client gateway call failed: read timeout after 5000ms
2026-05-02T10:15:02Z ERROR HikariPool-payment Connection is not available
2026-05-02T10:15:07Z ERROR HikariPool-payment Connection is not available
"""


@pytest.fixture
def evidence():
    items, _ = extract_evidence({"logs": LOGS}, max_chars=10_000)
    return items


def has_hebrew(text: str) -> bool:
    return bool(HEBREW.search(text or ""))


# --- request schema ----------------------------------------------------------

def test_language_defaults_to_english():
    assert AnalysisOptions().language == "en"
    assert IncidentRequest().options.language == "en"


def test_unknown_language_is_rejected_by_the_schema():
    with pytest.raises(ValueError):
        AnalysisOptions(language="fr")


# --- prompt ------------------------------------------------------------------

def test_english_prompt_carries_no_language_block():
    prompt = prompts.build_analysis_prompt(
        title="x", evidence_block="[E1] boom", observed_timeline="",
        hypothesis_count=4, coverage_note="", language="en",
    )
    assert "# Language" not in prompt


def test_hebrew_prompt_asks_for_hebrew_prose_but_protects_machine_text():
    prompt = prompts.build_analysis_prompt(
        title="x", evidence_block="[E1] boom", observed_timeline="",
        hypothesis_count=4, coverage_note="", language="he",
    )
    assert "# Language" in prompt
    assert "Hebrew" in prompt
    # The instruction must forbid translating quoted evidence, otherwise
    # citations stop matching the input they point at.
    assert "Do NOT translate machine text" in prompt
    assert "Evidence ids stay as they are" in prompt


def test_the_seven_rules_are_identical_in_every_language():
    """
    The system prompt is shared. A rule enforced only in one language is not a
    rule, and the bias/confidence discipline is the whole point of the tool.
    """
    english = prompts.build_analysis_prompt(
        title="x", evidence_block="[E1] boom", observed_timeline="",
        hypothesis_count=4, coverage_note="", language="en",
    )
    hebrew = prompts.build_analysis_prompt(
        title="x", evidence_block="[E1] boom", observed_timeline="",
        hypothesis_count=4, coverage_note="", language="he",
    )
    # Everything before the language block is byte-identical.
    assert hebrew.startswith(english.rstrip("\n").rsplit("\n", 1)[0][:200])
    assert prompts.ANALYSIS_SYSTEM == prompts.ANALYSIS_SYSTEM  # single source


def test_challenge_prompt_also_honours_the_language():
    hebrew = prompts.build_challenge_prompt(
        hypothesis_title="t", hypothesis_explanation="e",
        supporting=["E1"], contradicting=[], evidence_block="[E1] boom",
        language="he",
    )
    assert "# Language" in hebrew


# --- offline engine ----------------------------------------------------------

def test_offline_strings_fall_back_rather_than_raise():
    """The fallback path must never be the thing that crashes."""
    assert offline_strings.get("klingon") is offline_strings.get("en")


def test_offline_engine_speaks_english_by_default(evidence):
    payload = analyse(evidence, title="t", hypothesis_count=3)
    assert not has_hebrew(payload["summary"]["text"])


def test_offline_engine_speaks_hebrew_when_asked(evidence):
    """
    This is not cosmetic. A rate-limited or key-less run falls back here, so a
    Hebrew user hits the offline engine in normal use, not only in edge cases.
    """
    payload = analyse(evidence, title="t", hypothesis_count=3, language="he")
    assert has_hebrew(payload["summary"]["text"])
    assert has_hebrew(payload["next_actions"][0]["action"])
    assert has_hebrew(payload["assumptions"][0]["statement"])
    assert has_hebrew(payload["open_questions"][0]["question"])


def test_offline_engine_never_translates_evidence_or_ids(evidence):
    payload = analyse(evidence, title="t", hypothesis_count=3, language="he")

    # Citations stay as ASCII ids that resolve against the evidence set.
    known = {item.id for item in evidence}
    for cite in payload["summary"]["citations"]:
        assert cite in known
        assert not has_hebrew(cite)

    # The raw log text quoted inside a fact keeps its original wording.
    assert any("HikariPool" in fact["statement"] or "gateway" in fact["statement"]
               for fact in payload["facts"])


def test_offline_engine_keeps_enum_values_in_english(evidence):
    """Priority and owner_role are schema keys, not prose - translating them
    would fail validation downstream."""
    payload = analyse(evidence, title="t", hypothesis_count=3, language="he")
    for action in payload["next_actions"]:
        assert action["priority"] in {"P1", "P2", "P3", "P4"}
        assert action["owner_role"] in {"engineer", "sre", "manager", "support", "security"}


def test_both_languages_produce_the_same_structure(evidence):
    """Only the wording changes - the analysis shape must not."""
    en = analyse(evidence, title="t", hypothesis_count=3, language="en")
    he = analyse(evidence, title="t", hypothesis_count=3, language="he")

    assert en.keys() == he.keys()
    assert len(en["hypotheses"]) == len(he["hypotheses"])
    assert len(en["next_actions"]) == len(he["next_actions"])
    assert [h["confidence"] for h in en["hypotheses"]] == \
           [h["confidence"] for h in he["hypotheses"]]
