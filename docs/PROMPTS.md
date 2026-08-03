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

Three are supported directly. Results below are from our own runs; the reference
run referred to throughout is [`data/samples/example-output.md`](../data/samples/example-output.md)
— `checkout-v241` through `gemini-2.5-flash`, 59 evidence items, 29 checkable
claims, grounding 100%.

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

**We could not run this one.** Only `GEMINI_API_KEY` was configured, so
`compare_models.py` had a single provider and nothing to compare it against. No
results are reported for it, because there are none.

What we ran instead was the control condition: the same incident with the model
removed entirely. That is a weaker experiment in one sense — the offline engine
is not a second opinion, it is a floor — but it isolates the AI's contribution
more cleanly than a model-versus-model diff would.

| Measure | Offline engine | gemini-2.5-flash |
|---|---|---|
| Leading hypothesis | *"The failure is centred on: ERROR HikariPool-payment connection is not available…"* | *"v2.4.1's pooled client and retry logic exhaust connections under rising upstream gateway latency"* |
| Top confidence | 0.32 | 0.75 |
| Hypotheses carrying disconfirming evidence | 0 of 4 | 3 of 4 |
| Counter-argument | — | identifies the E57 double-charge the leader cannot explain |

The offline engine finds *where* errors cluster; it never proposes a mechanism
and never argues with itself. Causal structure and disconfirmation are what the
model adds.

**What to look for if you do add a second key:** disagreement is the finding.
When two independent models read the same evidence and reach different
conclusions, neither conclusion is "what the evidence supports" — it is what that
model believes. Agreement is weaker evidence than it feels: both models share
training data and both are susceptible to the same framing in the prompt.

### 4.2 Small prompt changes, different answers

Edit one rule in `ANALYSIS_SYSTEM`, re-run the same sample, and diff the output.
Suggested single-variable changes:

| Change | Hypothesis to test |
|---|---|
| Delete the confidence cap in rule 5 | Confidence values rise and stop discriminating |
| Delete "at least one hypothesis must NOT blame the most recent deployment" | All hypotheses converge on the deploy in `checkout-v241` |
| Delete "reporting none is acceptable" from rule 6 | The bias section fills with generic entries |
| Change "several competing explanations" to "the most likely explanation" | A single answer, presented with more certainty |

Four were run during development, each after observing the failure it was meant
to fix:

| Change tested | Sample | Before | After | Conclusion |
|---|---|---|---|---|
| Added "at least one hypothesis must NOT blame the most recent deployment" (rule 3) | checkout-v241 | All four hypotheses blamed release v2.4.1 — four rewordings of one answer | H2 is external gateway degradation, H4 internal resource contention; the summary notes latency was climbing *before* the deploy | The model had the contradicting evidence the whole time and cited it once asked. The failure was not a knowledge gap — nothing had required it to look |
| Capped confidence at 0.75 unless independent evidence agrees (rule 5) | all three | 0.85–0.95 regardless of support; ranking carried no information | Reference run spreads 0.75 / 0.60 / 0.50 / 0.20 | Confidence became a signal rather than a tone of voice |
| Rewrote rule 4 so an empty contradicting list is "a **claim that you looked**" | all three | `contradicting_evidence` empty on nearly every hypothesis | 3 of 4 hypotheses carry real disconfirming evidence | The field turned from a default into an assertion — and where it *is* empty, the confirmation-bias rule now fires meaningfully |
| Added "reporting none is acceptable and preferable to inventing one" (rule 6) | all three | Four or five generic biases reported every run | Reference run reports three, each pointing at a specific place in the analysis | Bias-theatre stopped |

### 4.3 Ask the model to argue against itself

Already built in — the *Argue against the leading hypothesis* checkbox. Compare
the rebuttal against the analysis it critiques:

- Does the rebuttal cite evidence the analysis ignored?
- Does it concede immediately, or construct a real alternative?
- Does running it change your confidence in the leading hypothesis?

| Sample | Rebuttal quality (real / hedged / conceded) | Did it change your view? |
|---|---|---|
| checkout-v241 | **Real.** It found that H1 cannot explain E57 — the customer charged twice — since a connection merely consumed for five seconds and failed should not produce a charge. It then proposed a concrete alternative mechanism (the gateway processing requests past our 5s timeout while retry logic starts new attempts) and named the falsifying observation: check gateway logs for the transactions behind E8/E9/E10 and see whether they are true failures or delayed successes | Yes. H1 had shipped with an empty "evidence against" column, and the rebuttal supplied the disconfirming evidence the main pass had not gone looking for. It did not overturn the hypothesis, but it removed the impression that nothing argued against it |

---

## 5. Recording hallucinations

The tool records them for you. Every analysis carries a `verification` block.
Here is the one from the reference run:

```json
"verification": {
  "claims_checked": 29,
  "unsupported": [],
  "invalid_citations": [],
  "grounding_score": 1.0
}
```

An entry in `invalid_citations` is a **caught hallucination**: the model cited an
evidence item that does not exist, and the shape is
`{"citation": "E42", "where": "facts[3]"}` for input that stops at E31.

**We did not observe one.** Across the runs we recorded, every citation resolved
to a real evidence ID. That is reported as the result rather than hunted past
until something broke — and it is worth being precise about what it does and does
not show. It does not mean the model cannot fabricate; it means that on this
input, with the IDs supplied in the prompt and a schema constraining the output,
it did not. Nor does 100% grounding mean the analysis is correct: a citation can
point at a real line and still misread it.

Full write-up in [`AI_USAGE_LOG.md`](AI_USAGE_LOG.md).
