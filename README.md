# IncidentIQ

An AI-assisted incident-response and root-cause analysis tool.

IncidentIQ takes the messy evidence produced by a production incident — logs,
error traces, monitoring alerts, deployment notes, support tickets — and turns
it into a structured investigation: a timeline, a ranked set of root-cause
hypotheses with evidence *for and against* each one, a reasoning-risks report,
concrete next debugging steps, and a draft postmortem.

The point is **not** to let the AI decide the answer. The point is to keep facts,
assumptions, hypotheses and actions separate, and to make every AI claim
traceable back to a specific piece of input evidence.

---

## Status

Work in progress. This README is filled in as the project is built.

## Planned structure

```
IncidentIQ/
├── backend/          FastAPI service + analysis engine
├── frontend/         Zero-build UI (HTML + CSS + ES modules)
├── data/samples/     Example incident datasets
├── docs/             Prompt library and the reflective report
└── tests/            Unit tests for the deterministic parts
```

## Setup (draft)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env         # then fill in one API key
```

Leaving the API key blank is supported: IncidentIQ then runs in **offline mode**
and uses only its deterministic analysis engine, which is useful for grading and
for demonstrating what the AI actually adds.
