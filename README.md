# IncidentIQ

An AI-assisted incident-response and root-cause analysis tool.

IncidentIQ takes the messy evidence a production incident leaves behind — logs,
error traces, monitoring alerts, deployment notes, support tickets — and turns it
into a structured investigation: a numbered evidence set, a timeline, several
competing root-cause hypotheses with evidence *for and against* each one, a
reasoning-risks report, prioritised next steps, and a draft postmortem.

**The point is not to let the AI decide the answer.** The tool keeps facts,
assumptions, hypotheses and actions apart, makes every AI claim cite the exact
input line it rests on, and checks those citations before you ever read them.

---

## Run it

### Windows — double-click `run.bat`

That is the whole procedure. On first run it creates a virtual environment,
installs the dependencies, starts the server and opens your browser at
<http://127.0.0.1:8000>.

### macOS / Linux

```bash
chmod +x run.sh    # once
./run.sh
```

### Manually, if you prefer

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
python run.py
```

### It works without an API key

If `.env` has no key, IncidentIQ runs in **offline mode**: it still indexes the
evidence, builds the timeline and ranks error clusters, but it cannot do causal
reasoning or the bias audit. Every screen says so, in the header badge and in a
banner on the summary. Nothing produced offline can be mistaken for model output.

To enable the full analysis, open `.env` and fill in one key:

```ini
ANTHROPIC_API_KEY=sk-ant-...
```

`.env` is created automatically from `.env.example` on first run, and is
git-ignored.

---

## Using it

1. **Pick an example incident** from the left panel, or paste your own evidence.
   The six input fields map to the six input types in the brief; they stay
   separate because "the deploy notes say X" is a different kind of claim from
   "a user says X".
2. **Press Analyse incident.** Two options are on by default:
   - *Argue against the leading hypothesis* — a second pass that tries to
     falsify the top answer rather than support it.
   - *Redact emails, IPs and tokens* — nothing secret-shaped leaves your machine.
3. **Read the tabs in order.** They are ordered as an argument:

| Tab | What it answers |
|---|---|
| Summary | How trustworthy is this analysis, and what happened? Verification comes *before* the summary, deliberately. |
| Evidence | Every input line, numbered. This is the ground truth everything else cites. |
| Timeline | What we observed, versus what someone inferred. Dashed markers are deductions. |
| Hypotheses | Competing explanations, ranked but not chosen, each with a test that would settle it. |
| Reasoning risks | How *this investigation* may be going wrong. |
| Next actions | What to do, each tied to the evidence that motivates it. |
| Postmortem | A draft you can export as Markdown. |

Click any `E7`-style pill anywhere in the app to jump to that exact input line.
A citation shown **in red** points at an evidence item that does not exist — the
model invented it, and the tool is telling you.

---

## How it works

```
 browser (zero-build ES modules)
     │  POST /api/analyze
     ▼
 FastAPI  ──►  redact  ──►  extract evidence  ──►  observed timeline
                                                          │
                             ┌────────────────────────────┘
                             ▼
                     model pass (Anthropic / OpenAI)
                             │           │
                             │           └──► offline engine, if no key or on failure
                             ▼
                        verify citations
                             ▼
                     challenge pass (devil's advocate)
                             ▼
                  rule-based bias detection  ──►  merge with the model's self-audit
                             ▼
                    assemble + render postmortem
```

Two design decisions carry most of the weight:

**Evidence IDs are assigned before the model sees anything.** The input is split
into numbered items `E1..En` by a deterministic parser. The model is shown those
IDs and told to cite them. Afterwards, every citation is checked against the set
that actually exists. A citation to `E42` when the input stops at `E31` is a
fabrication, and it is caught mechanically rather than by a reader noticing.

**Bias detection does not rely on the model auditing itself.** Asking a model to
find its own bias is circular. Eight deterministic rules examine the *shape* of
the analysis instead — confidence versus citation count, which evidence is cited
and which is ignored, whether a deploy-blaming hypothesis has any log line
linking the deploy to the failure. Where a rule and the model agree, the finding
is labelled *rule + model*.

---

## Layout

```
IncidentIQ/
├── run.bat / run.sh / run.py    one-click launcher
├── backend/
│   ├── main.py                  FastAPI app; also serves the frontend
│   ├── config.py                environment, read exactly once
│   ├── api/routes.py            HTTP layer (parse, delegate, serialise)
│   ├── models/                  typed request and response schemas
│   └── services/
│       ├── redaction.py         strips secret-shaped values pre-flight
│       ├── evidence.py          text -> numbered, citable items
│       ├── timeline.py          observed events only, never inferred
│       ├── llm/                 provider abstraction (Anthropic / OpenAI)
│       ├── prompts.py           every instruction sent to a model
│       ├── biases.py            the eight biases from the brief
│       ├── verifier.py          grounding check
│       ├── risk_detector.py     rule-based bias detection
│       ├── offline_engine.py    the no-model analysis
│       ├── analyzer.py          the pipeline
│       └── report.py            Markdown postmortem
├── frontend/                    HTML + CSS + ES modules, no build step
├── data/samples/                example incidents (drop in a .json)
├── docs/                        prompt library, AI usage log, report
└── tests/                       49 tests, none of which call a model
```

## Tests

```bash
.venv\Scripts\python -m pytest
```

## Configuration

Everything lives in `.env` and is documented in `.env.example`. The settings you
are most likely to touch:

| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` | `anthropic`, `openai`, or `offline` |
| `ANTHROPIC_MODEL` | `claude-opus-4-8` | `claude-sonnet-5` is cheaper and adequate |
| `HYPOTHESIS_COUNT` | `4` | how many competing explanations to require |
| `REDACT_PII` | `true` | strip secret-shaped values before any provider call |
| `MAX_INPUT_CHARS` | `120000` | per-analysis input cap, truncated per source |

## AI tools used

| Tool | Used for |
|---|---|
| Anthropic Claude (`claude-opus-4-8`) | The analysis and challenge passes at runtime; the bulk of development assistance |
| OpenAI (`gpt-4o`) | Optional second provider, used for the cross-model comparison in `docs/PROMPTS.md` |

The prompts the system sends are in `backend/services/prompts.py` and are
reproduced with commentary in `docs/PROMPTS.md`. Where AI helped during
development, and where it misled us, is recorded in `docs/AI_USAGE_LOG.md`.

## Limitations

Stated plainly, because a tool about epistemic honesty should not oversell
itself:

- **Grounding is not accuracy.** The verifier proves a claim cites a real input
  line. It cannot tell whether the claim reads that line correctly.
- **Redaction is pattern matching.** It catches values with a recognisable shape.
  It cannot tell that "customer 88213 requested deletion" is personal data.
- **The bias rules only see what was written down.** Reasoning the model did not
  express is invisible to them, so "no risks flagged" is weaker evidence than it
  looks — the UI says so.
- **Nothing here confirms a root cause.** Every hypothesis carries a test. Run
  the test.
