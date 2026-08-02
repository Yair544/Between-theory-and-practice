# The prompt library

Every instruction IncidentIQ sends to a model lives in
[`backend/services/prompts.py`](../backend/services/prompts.py). This document
explains *why* each part is there and how to run the experiments the brief asks
for.

---

## 1. The three prompts

| Prompt | Call | Purpose |
|---|---|---|
| `ANALYSIS_SYSTEM` + `build_analysis_prompt()` | 1 per analysis | The structured investigation |
| `CHALLENGE_SYSTEM` + `build_challenge_prompt()` | 1 per analysis, optional | Argue against the leading hypothesis |
| The `audiences` field of the analysis schema | included in call 1 | Rewrite for engineer / manager / support |

The challenge prompt is a **separate API call with a fresh context**, not a
follow-up turn. This is the single most important structural choice in the
prompt design. A model asked "now criticise what you just said" is still
completing its own train of thought and tends to produce a polite, hedged
critique that concedes the original point. A model handed an analysis it has
never seen, told it has no stake in it, and asked to attack it, produces a
different kind of output.

---

## 2. The seven rules, and what each one is defending against

`ANALYSIS_SYSTEM` is built around seven numbered rules. Each exists because of a
specific failure mode.

| Rule | Failure it prevents |
|---|---|
| 1. Cite evidence IDs; never cite an ID that is not in the input | Untraceable claims. This is what makes the verifier possible at all — without enforced IDs there is nothing to check. |
| 2. Keep facts / assumptions / hypotheses / actions separate | The single biggest failure of AI incident summaries: a guess written in the grammatical form of a fact. |
| 3. Never claim a root cause; always give a genuine alternative | A single confident answer ends the investigation. The clause "including at least one that does not involve the most recent deployment" is aimed directly at post hoc reasoning. |
| 4. Actively search for disconfirming evidence | Confirmation bias. The wording "an empty contradicting list is a claim that you looked" matters — without it, the field is simply left empty by default. |
| 5. Confidence is evidential, capped at 0.75 | Overconfidence. Models produce fluent, high-certainty prose regardless of evidence quality. The cap forces the number to mean something. |
| 6. Audit your own reasoning against the catalogue; reporting none is acceptable | Bias-theatre. Without the escape clause, a model asked to find biases will always find some, which makes the section worthless. |
| 7. Say so in `open_questions` rather than inventing | Hallucination under pressure to be complete. |

### Rules that were tightened during development

Recording these because the brief asks for prompt iterations, and because the
first drafts failed in instructive ways.

**Rule 4 originally read** *"list evidence that contradicts each hypothesis"*.
That produced empty `contradicting_evidence` arrays on almost every hypothesis —
the field was treated as optional. Rewriting it as *"An empty contradicting list
is a claim that you looked and found nothing — do not use it as a default"*
converts an omission into an assertion the model has to be willing to make.

**Rule 5 originally had no ceiling.** Confidence values clustered at 0.85–0.95
and stopped discriminating between hypotheses. The explicit cap plus the
condition ("unless multiple independent evidence items point the same way and
none contradict") restored the spread.

**Rule 6 originally lacked the escape clause.** Every run returned four or five
biases, several of which were generic ("there is a risk of confirmation bias in
any investigation"). Adding *"Do not report a bias you cannot point at.
Reporting none is acceptable and preferable to inventing one"* cut the noise.

**Rule 3's deployment clause was added after the `checkout-v241` sample.** Early
runs on that incident produced four hypotheses, all four of which blamed release
v2.4.1 — which is what the sample is designed to bait. Four variations on one
answer is not four hypotheses.

---

## 3. Structured output rather than prose parsing

The analysis is requested as a JSON object against
[`ANALYSIS_SCHEMA`](../backend/services/prompts.py). This removes an entire class
of failure ("the model wrote a nice paragraph instead of the object") and, more
importantly, makes the four statement types *structurally* separate: there is no
field where a hypothesis can be written as a fact.

`base.py` still parses tolerantly (code fences, prose around the object), and
reports every repair as a warning. A silent repair is how you stop noticing that
a prompt has quietly stopped working.

---

## 4. Experiments the brief asks for

Three are supported directly. **Run them yourself and record the results** — the
tables below are deliberately empty, because a prompt experiment written up from
someone else's numbers is not an experiment.

### 4.1 Same prompt, two models

```bash
.venv\Scripts\python tools\compare_models.py checkout-v241
```

Requires keys for at least two of `GEMINI_API_KEY`, `ANTHROPIC_API_KEY` and
`OPENAI_API_KEY` in `.env`. It runs the identical prompt through each configured
provider and prints a comparison of leading hypothesis, confidence, citation
overlap and grounding score.

Gemini is the default provider, so the cheapest second opinion to add is an
Anthropic or OpenAI key.

| Sample | Model A leading hypothesis | Model B leading hypothesis | Agree? | Grounding A / B |
|---|---|---|---|---|
| checkout-v241 | | | | |
| registration-peak | | | | |
| booking-intermittent-500 | | | | |

**What to look for:** disagreement is the finding. When two independent models
read the same evidence and reach different conclusions, neither conclusion is
"what the evidence supports" — it is what that model believes. Agreement is
weaker evidence than it feels: both models share training data and both are
susceptible to the same framing in the prompt.

### 4.2 Small prompt changes, different answers

Edit one rule in `ANALYSIS_SYSTEM`, re-run the same sample, and diff the output.
Suggested single-variable changes:

| Change | Hypothesis to test |
|---|---|
| Delete the confidence cap in rule 5 | Confidence values rise and stop discriminating |
| Delete "at least one hypothesis must NOT blame the most recent deployment" | All hypotheses converge on the deploy in `checkout-v241` |
| Delete "reporting none is acceptable" from rule 6 | The bias section fills with generic entries |
| Change "several competing explanations" to "the most likely explanation" | A single answer, presented with more certainty |

| Change tested | Sample | Before | After | Conclusion |
|---|---|---|---|---|
| | | | | |

### 4.3 Ask the model to argue against itself

Already built in — the *Argue against the leading hypothesis* checkbox. Compare
the rebuttal against the analysis it critiques:

- Does the rebuttal cite evidence the analysis ignored?
- Does it concede immediately, or construct a real alternative?
- Does running it change your confidence in the leading hypothesis?

| Sample | Rebuttal quality (real / hedged / conceded) | Did it change your view? |
|---|---|---|
| | | |

---

## 5. Recording hallucinations

The tool records them for you. Every analysis carries a `verification` block:

```json
"verification": {
  "claims_checked": 24,
  "unsupported": [...],
  "invalid_citations": [{"citation": "E42", "where": "facts[3]"}],
  "grounding_score": 0.88
}
```

An entry in `invalid_citations` is a **caught hallucination**: the model referred
to an evidence item that does not exist. These are worth pasting verbatim into
the reflective report, since they are the clearest possible demonstration of the
brief's point about verifying AI claims rather than trusting them.

Keep a log in [`AI_USAGE_LOG.md`](AI_USAGE_LOG.md) as you run.
