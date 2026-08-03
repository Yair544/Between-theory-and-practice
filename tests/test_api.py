"""
End-to-end tests through the HTTP layer.

These run in offline mode - pinned there by the `_force_offline` fixture in
conftest, not left to whether a key happens to be configured. That is exactly
the path a marker takes on first launch, so the suite doubles as a check that
the no-credentials experience works.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.llm import LLMError, parse_json_object


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# --- basics ------------------------------------------------------------------

def test_health_never_leaks_a_key(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert set(body) >= {"provider", "model", "offline", "has_anthropic_key"}
    assert not any("sk-" in str(value) for value in body.values())


def test_frontend_is_served_by_the_same_process(client):
    assert client.get("/").status_code == 200
    assert client.get("/css/theme.css").status_code == 200
    assert client.get("/js/app.js").status_code == 200


def test_samples_are_listed_and_fetchable(client):
    listed = client.get("/api/samples").json()
    assert listed, "the bundled example incidents should be discoverable"
    sample = client.get(f"/api/samples/{listed[0]['id']}").json()
    assert sample["title"]
    assert client.get("/api/samples/does-not-exist").status_code == 404


def test_bias_catalog_matches_the_brief(client):
    ids = {entry["id"] for entry in client.get("/api/biases").json()}
    assert ids == {
        "confirmation_bias", "anchoring_bias", "automation_bias", "post_hoc",
        "availability_bias", "overconfidence_bias", "hindsight_bias", "base_rate_neglect",
    }


# --- analyse -----------------------------------------------------------------

def test_empty_input_is_rejected_with_a_useful_message(client):
    response = client.post("/api/analyze", json={"title": "x"})
    assert response.status_code == 400
    assert "10 or more characters" in response.json()["detail"]


def test_analysis_of_a_bundled_sample(client):
    sample = client.get("/api/samples/checkout-v241").json()
    response = client.post("/api/analyze", json={
        "title": sample["title"],
        "description": sample["description"],
        "logs": sample["logs"],
        "errors": sample["errors"],
        "alerts": sample["alerts"],
        "deploy_notes": sample["deploy_notes"],
        "user_reports": sample["user_reports"],
    })
    assert response.status_code == 200
    body = response.json()

    assert len(body["evidence"]) > 20
    assert body["timeline"], "timestamped logs should produce a timeline"
    assert len(body["hypotheses"]) >= 2, "the tool must never return a single answer"
    assert body["report_markdown"].startswith("# Incident postmortem (DRAFT)")
    assert len(body["bias_catalog"]) == 8


def test_every_citation_in_the_response_resolves(client):
    """
    The whole design rests on this: after the pipeline runs, no rendered claim
    may point at an evidence id that does not exist.
    """
    sample = client.get("/api/samples/registration-peak").json()
    body = client.post("/api/analyze", json={
        "title": sample["title"], "logs": sample["logs"], "alerts": sample["alerts"],
        "deploy_notes": sample["deploy_notes"],
    }).json()

    known = {item["id"] for item in body["evidence"]}
    cited: list[str] = list(body["summary"]["citations"])
    for fact in body["facts"]:
        cited += fact["evidence"]
    for hypothesis in body["hypotheses"]:
        cited += hypothesis["supporting_evidence"] + hypothesis["contradicting_evidence"]
    for action in body["next_actions"]:
        cited += action["evidence"]
    for event in body["timeline"]:
        cited += event["evidence"]

    assert cited, "the analysis should cite something"
    assert set(cited) <= known


def test_report_can_be_fetched_by_id(client):
    body = client.post("/api/analyze", json={
        "title": "Test", "logs": "2026-01-01T00:00:00Z ERROR everything is on fire",
    }).json()
    report = client.get(f"/api/analysis/{body['id']}/report.md")
    assert report.status_code == 200
    assert "Verification of AI claims" in report.text
    assert client.get("/api/analysis/deadbeef/report.md").status_code == 404


def test_offline_mode_is_declared_in_the_response(client):
    """A run without a model must be impossible to mistake for one with a model."""
    health = client.get("/api/health").json()
    body = client.post("/api/analyze", json={
        "title": "Test", "logs": "2026-01-01T00:00:00Z ERROR everything is on fire",
    }).json()
    assert body["meta"]["offline"] is health["offline"]


# --- JSON recovery -----------------------------------------------------------

def test_code_fence_is_unwrapped_with_a_warning():
    payload, warnings = parse_json_object('```json\n{"a": 1}\n```')
    assert payload == {"a": 1}
    assert warnings, "a silent repair is how you stop noticing a broken prompt"


def test_prose_around_the_object_is_stripped():
    payload, warnings = parse_json_object('Sure! Here it is:\n{"a": 1}\nHope that helps.')
    assert payload == {"a": 1}
    assert warnings


def test_unrecoverable_output_raises_a_readable_error():
    with pytest.raises(LLMError) as exc:
        parse_json_object("I am afraid I cannot do that.")
    assert "MAX_OUTPUT_TOKENS" in str(exc.value)
