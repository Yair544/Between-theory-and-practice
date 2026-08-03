# IncidentIQ — Reflective Report

**Course:** Computer Science — Critical Thinking, Problem Solving and 21st-Century Skills
**Project:** IncidentIQ — an AI-powered incident response and root-cause analysis tool
**Authors:** Ofek Revach · Yair Markovski
**GitHub:** https://github.com/Yair544/Between-theory-and-practice
**Demo video:** https://drive.google.com/file/d/1KPN79sRCxPNyKru3YtrLTYIus_lmCUpb/view?usp=sharing
**Date:** 3 August 2026

---

## 1. Project overview and purpose

IncidentIQ helps a development or SRE team investigate a production incident. It
accepts the evidence an incident actually produces — application logs, error
traces, monitoring alerts, deployment notes, user complaints — and produces a
structured investigation: a numbered evidence set, a reconstructed timeline,
several competing root-cause hypotheses with evidence for *and against* each one,
a reasoning-risks report, prioritised next steps, and a draft postmortem.

The design question was not "how do we get an AI to find the root cause". It was
the opposite: **how do we build a tool that uses AI heavily without letting the AI
decide?** Three commitments follow, and they shape every part of the system:

1. **Facts, assumptions, hypotheses and actions are structurally separate** — four
   distinct types in the schema, not four sections of one text field. The engine
   cannot return a guess in the slot where a fact belongs.
2. **Every AI claim must cite the specific input line it rests on**, and those
   citations are verified mechanically before a human reads them.
3. **The tool never claims a root cause.** It ranks hypotheses and attaches to each
   a concrete test that would confirm or kill it. Confirming a cause is a human
   decision made after running that test.

---

## 2. System architecture and main features

**Pipeline (order is fixed, each step depends on the previous):**
redact → extract evidence → observed timeline → model pass (or offline engine) →
verify citations → challenge pass → rule-based bias detection → merge with the
model's self-audit → assemble + render postmortem.

Redaction runs first so nothing sensitive reaches a provider. Evidence extraction
runs second so IDs exist before the model does anything. Verification runs before
the challenge pass so the devil's advocate argues against already-clean citations.

### 2.1 The two ideas that carry the design

**Evidence IDs assigned before the model sees anything.** A deterministic parser
splits input into numbered items `E1..En`. The model is shown those IDs and
required to cite them; afterwards every citation is checked against the set that
actually exists. A citation to `E42` when input stops at `E31` is a fabrication
caught by a set-membership test rather than by a reader noticing — the difference
between "the AI said so" and something a reviewer can check in five seconds.

**Bias detection that does not depend on the model auditing itself.** Asking a
model to find bias in its own output is circular. So the eight biases from the
brief are also checked by deterministic rules reading the *shape* of the analysis:

| Bias / fallacy | What the rule looks at |
|---|---|
| Confirmation bias | Supporting evidence present, contradicting list empty |
| Anchoring bias | Leading hypothesis citing only the first fifth of the input |
| Post hoc fallacy | Deploy-blaming hypothesis whose only citations are deployment notes |
| Overconfidence | Confidence ≥ 0.75 on fewer than three citations |
| Availability bias | A stock cause ("memory leak", "DNS") appearing nowhere in the input |
| Base-rate neglect | A log pattern repeating 5+ times that no hypothesis mentions |
| Hindsight bias | "Obviously"/"clearly" applied to a cause nobody knew at the time |
| Automation bias | Confident leading hypothesis in a run that failed the grounding check |

Where a rule and the model flag the same bias, the finding is labelled
*rule + model* — the strongest signal the tool produces.

### 2.2 Features against the brief's requirements

| Required feature | How it is met |
|---|---|
| Input interface | Six fields (description, logs, traces, alerts, deploy notes, user reports), paste or upload, plus three bundled samples |
| AI-powered summary | Structured summary with citations; verification banner shown *above* it |
| Timeline reconstruction | Deterministic timeline from parsed timestamps marked *observed*; model-added events marked *inferred* with dashed markers |
| Hypothesis generator | N competing hypotheses (default 4), each with confidence, evidence for, evidence against, recommended test |
| Bias and fallacy detector | All eight, checked by rules and by the model, merged |
| Suggested next actions | Prioritised, each citing motivating evidence; ungrounded ones marked "generic advice" |
| Draft postmortem | Markdown export with verification numbers included, not buried |

Beyond basic scope: file upload, evidence-source filtering, role-based rewrites
(engineer / manager / support), unsupported-claim detection, a devil's-advocate
pass, PII redaction, an offline mode, a cross-model comparison tool, and a full
Hebrew interface with right-to-left layout.

**On the Hebrew mode**, one decision follows from the same principle as the rest:
the interface and the model's prose are translated; the evidence is not. A log line
quoted back in Hebrew is no longer a quotation — it cannot be matched against the
input, so the verifier could not check it and the citation would become
decorative. Machine text (log lines, traces, timestamps, evidence IDs) stays in
its original wording and direction even inside a Hebrew page.

---

## 3. Technologies used

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.10+, FastAPI, Pydantic v2 | Typed schemas that double as validation and API contract |
| Frontend | HTML + CSS + native ES modules, **no build step** | The tool must start with one double-click on a machine we do not control |
| AI | Google Gemini (`gemini-2.5-flash`) primary; Claude and GPT selectable | Behind a provider interface; switching model is one line in `.env` |
| Config | `python-dotenv` | Keys live in `.env`, never in git |
| Tests | pytest — 73 tests, none calling a model | Deterministic layers testable without an API key |

React would have been faster to write, but would have meant a build step and a
version of the app that can be stale relative to the backend. For a tool whose
grading path is "double-click `run.bat`", plain modules were the more defensible
decision, at a cost of ~200 lines of DOM helpers.

---

## 4. How AI was used

### 4.1 Inside the product

Three calls, all defined in `backend/services/prompts.py`:

1. **The analysis pass** — one structured call producing the whole investigation
   against a JSON schema.
2. **The challenge pass** — a *separate* call with a fresh context, told it is a
   skeptical reviewer with no stake in the analysis, asked to argue the leading
   hypothesis is wrong. Deliberately not a follow-up turn: a model asked "now
   criticise yourself" is still completing its own train of thought and tends to
   produce a polite critique that concedes the point.
3. **Audience rewrites** — part of the analysis schema rather than a third call, so
   the manager version cannot quietly acquire certainty the engineer version lacks.

Full prompt text and rationale: `docs/PROMPTS.md`.

### 4.2 Prompt iterations

Four changes, each made after observing a specific failure:

| Symptom observed | Change | Effect |
|---|---|---|
| `contradicting_evidence` empty on nearly every hypothesis | Rule 4 rewritten: an empty list is "a **claim that you looked**" | The field became an assertion rather than an omission |
| Confidence clustered at 0.85–0.95 | Rule 5 capped confidence at 0.75 unless independent evidence agrees | Spread restored; the number started meaning something |
| Four or five generic biases every run | Rule 6 gained "reporting none is acceptable and preferable to inventing one" | Bias-theatre stopped |
| All four hypotheses blamed release v2.4.1 | Rule 3 gained "at least one hypothesis must NOT blame the most recent deployment" | Four variations on one answer became four hypotheses |

The last is the interesting case: the sample is *designed* to bait post hoc
reasoning, the model took the bait, and the fix was a prompt constraint rather
than better model output.

### 4.3 Examples of useful AI output

**Synthetic incident data.** Writing 150 lines of plausible production logs by hand
is slow and the result is too clean. AI produced usable drafts in minutes. Almost
all our edits went one direction: putting the *mess* back in. The first versions
had every error neatly explaining itself, no red herrings, and a timeline where
cause visibly preceded effect — which would have made the tool look far better
than it is, because the hard part of incident analysis is exactly the noise the
model had smoothed away.

**Rewriting reasoning-risk explanations** from terse definitions into text an
on-call engineer would read at 2am. Useful for tone — though every claim about
*what the detector actually does* still had to be checked against the code,
because the model happily wrote confident descriptions of capabilities it did not
have. **Boilerplate** (Pydantic schemas, FastAPI routing, CSS tokens) was fast and
mostly correct — the category where AI assistance is least interesting and most
reliable.

### 4.4 Examples of incorrect, misleading or overconfident AI output

**A regex described correctly and behaving wrongly.** Three modules each needed to
group repeated log lines, and each got its own generated copy of a normalising
helper meant to blank digits so two timeouts a minute apart collapse into one
event. It did not work: `\b\d+\b` does not match `02Z`, because there is no word
boundary between a digit and a letter, so the seconds field survived and every
line stayed unique. The code *read* correctly, review passed it, and the bug only
surfaced when a 59-line sample produced 39 "distinct" timeline events that were
visibly repeats.

**A circular import that "should be fine".** Asked whether views importing
`registerView` from `app.js` while `app.js` imported the views was safe, the model
explained — correctly — that ES modules hoist function declarations. It was wrong
about *this* code, where the function closed over a `const` still in the temporal
dead zone. That shape of failure is the dangerous one: right about the mechanism,
wrong about the case, and a follow-up question gets the same
correct-in-general answer.

**A confidently false claim that reached the product.** While switching to Gemini,
the assistant told us — twice, unprompted, with no hedging — that our API key was
the wrong credential type: that Gemini keys begin `AIza` and a key beginning `AQ.`
was an OAuth token that would be rejected. All of it was wrong; Google issues more
than one valid key format. We deleted a working key on that advice and generated a
second one, which had the same prefix — the tell we did not read. Worse, the claim
had been written *into the product*: into the error message in `gemini_client.py`,
into `.env.example`, and into the README, where it would have told future users
the same falsehood. Verification took one API call, which we ran only after the
second key looked identical to the first.

---

## 5. How we tested and challenged the AI

| Method the brief asks for | How we did it |
|---|---|
| Check whether each AI claim is supported by the input | Automated: `verifier.py` checks every citation against the evidence set on every run |
| Compare multiple prompts or models | `tools/compare_models.py` runs identical input through every configured provider and diffs the leading hypothesis, citation overlap and grounding score |
| Ask the AI to argue against its own conclusion | Built into the product as the devil's-advocate pass |
| Test whether small prompt changes produce different answers | Single-variable experiments; procedure and results in `docs/PROMPTS.md` |
| Record hallucination and overconfidence | Every response carries a `verification` block; the overconfidence rule flags high-confidence/low-evidence hypotheses |
| Document where AI helped and where it misled | `docs/AI_USAGE_LOG.md` |

**The control condition.** The offline engine is not a stub — it is a real analysis
with no model involved. Running the same incident with and without a key isolates
what the AI actually contributed: the offline engine finds the error clusters, and
the model supplies the causal reasoning and the disconfirming evidence.

---

## 6. Problems encountered and how they were solved

| Problem | Solution |
|---|---|
| Models cite evidence that does not exist | IDs assigned deterministically before the model runs; every citation set-checked afterwards; invented ones shown in red and listed in the report |
| Models return prose around the JSON, or get cut off mid-object | Structured output requested from every provider, plus tolerant recovery that reports each repair as a warning — a silent repair is how you stop noticing a broken prompt |
| A model asked to self-audit for bias finds it everywhere, or nowhere | Independent deterministic rules; results merged and agreement labelled |
| Reasoning tokens starving the answer | On Gemini 2.5, thinking is billed against the same `max_output_tokens` ceiling as the answer. A 2000-token call spent 1805 on reasoning and 165 on the answer, truncating the JSON mid-string. Fixed by reserving half the budget via `thinking_config` |
| The tool must be gradeable without an API key | Offline engine, clearly labelled, with the launcher explaining what will and will not work |
| Confidence scores are meaningless by default | Capped in the prompt, banded in the UI; the top band is "well supported" — never "confirmed" |
| Sending production logs to a third party | Redaction before any provider call, on by default, count surfaced in the UI |

---

## 7. Cognitive biases and fallacies encountered

Implementing a detector is not the same as *encountering* the bias. These are the
five we actually met — three during development, two caught by the tool in a
recorded run.

**Post hoc fallacy — in the tool's output.** On the `checkout-v241` sample, early
runs produced four hypotheses and all four blamed release v2.4.1, deployed twelve
minutes before the first error. The sample is built so this is wrong: the latency
alert fires *fifteen minutes before* the deploy, and a partner using the same
payment provider reports the same slowness. The deploy shrank a safety margin; it
did not create the problem. We noticed by reading the evidence ourselves and
finding the 09:47 alert. Reduced by rule 3 in the system prompt (at least one
hypothesis must not involve the most recent change) plus a deterministic detector.

**Automation bias — in ourselves, twice.** First with the normalisation helper
above, accepted because it looked like the kind of code that works; we noticed
only when a sample produced 39 obviously-duplicate timeline events. Second, and
sharper, with the API key claim in §4.4 — we deleted a working key on a confident
assertion and caught it only against a Google Cloud Console screenshot. Both are
the same failure: fluent, specific, technical, and believed *because* of the
fluency. We reduced it with a standing rule that generated regexes get a test
before a review, and by making the corrected code refuse to assert which key
prefix is legitimate — the API is the authority on what the API accepts. This is
also why the tool raises automation bias as a *risk* whenever a confident answer
coexists with a failed grounding check.

**Overconfidence bias — in the tool's output.** Before the confidence cap,
hypotheses came back at 0.85–0.95 regardless of supporting evidence. We noticed
when the scores stopped discriminating — everything was "very likely", so the
ranking carried no information. Reduced with an explicit ceiling in the prompt, a
detector flagging high confidence on thin citations, and a UI that never uses the
word "confirmed".

**Confirmation bias and anchoring — caught by the tool in a recorded run.** The
run saved as `data/samples/example-output.md` (checkout-v241, gemini-2.5-flash,
59 evidence items, 100% grounding, 0 invalid citations) flagged both. The
*deterministic* rule caught confirmation bias: the leading hypothesis listed
supporting evidence and nothing contradicting — its confidence therefore
reflected the search, not the world. The *model's self-audit* caught anchoring:
it had focused on the "read timeout" and "Connection is not available" errors as
the primary symptoms, which risked missing an upstream cause. Both findings
survived our own reading of the evidence. Notably the same run did *not* fall for
the post hoc trap the sample is built around — it recorded that gateway latency
was already climbing before the deploy — which is the prompt constraint from
§4.2 working as intended.

---

## 8. Ethical and professional risks

**What could go wrong if engineers trust the tool too much.** The realistic failure
is not a wildly wrong answer — those get caught. It is a *plausible* wrong answer
delivered with citations, sending a team down a three-hour path while the real
cause keeps hurting users. The mitigations are structural: never one answer,
evidence against shown as prominently as evidence for, a falsifying test on every
hypothesis. None of that stops a tired engineer at 3am from reading only the top
card.

**Should the tool ever claim it found the root cause?** No, and it does not. A root
cause is confirmed by an experiment, not an argument. The strongest label is "well
supported"; the report header says DRAFT.

**How uncertainty is shown.** In more than one channel, because a single signal
gets tuned out: a numeric confidence *and* a band, distinct treatment for facts
versus assumptions, dashed markers for inferred events, an explicit warning when a
hypothesis has no contradicting evidence, and a grounding percentage always visible.

**What should not be sent to an external AI API.** Production logs routinely contain
emails, IPs, session tokens, sometimes payment data. `redaction.py` strips
recognisable shapes before any provider call, on by default. Its limits are stated
in the module docstring: it is pattern matching, so it catches an email and misses
"customer 88213 requested deletion". For genuinely sensitive systems the honest
answer is a local model or no model.

We learned this concretely rather than abstractly. Midway through, one of us pasted
an API credential directly into an AI chat window to speed up configuration —
having already written the module whose entire job is stopping secrets reaching a
third party. The key was revoked and reissued. The lesson generalises past our own
carelessness: **the safeguards a tool enforces do not govern the people operating
it.** A redaction pass on `POST /api/analyze` says nothing about what a tired
engineer pastes into a chat at 2am — and an incident-response tool is used mostly
by tired engineers.

**Who is responsible if the AI recommends a harmful action.** The person who runs
the command. That is not a disclaimer but a design constraint: it is why the
actions pane warns that a restart both fixes the problem and destroys the
evidence, and why no action in this tool is executable from the tool. The tool
supports human judgement rather than replacing it by being auditable rather than
authoritative — every claim is one click from the line it came from, and the
verification banner sits above the summary rather than in a footnote.

---

## 9. Division of work

Work was split by commit ownership rather than a plan drawn up in advance — each of
us took a vertical slice and carried it from first commit to working code. The
GitHub history is the record of this.

| Ofek | Yair |
|---|---|
| Scaffolding, env template, design system, application shell | Typed backend models and config |
| Frontend core modules (`dom`, `store`, `api`, `format`, `shell`) | Evidence extraction, timeline, redaction |
| Sample datasets and one-click launcher | LLM provider abstraction |
| Test suite (73 tests) | Bias catalogue and prompt library |
| README, prompt docs, AI usage log, this report | Grounding verifier and bias detectors |
| Visual polish and accessibility pass | Analysis pipeline and FastAPI service |
| Hebrew interface, RTL, Hebrew model output, branch merge | Reasoning views (hypotheses, risks, actions, postmortem) |

**How we worked.** We split along the natural seam in the architecture: Yair owned
everything from the API boundary inward, Ofek owned the frontend shell and the
surrounding layers. Working in parallel on separate halves of one schema meant the
main integration risk was the contract between them (the `Analysis` model), not
either half individually — Pydantic catching a shape mismatch at validation time
rather than at runtime is what kept that from being painful.

The one real conflict was mechanical: merging Yair's independently-pushed backend
commits with a later frontend commit surfaced a structural bug — a zip extracted
one directory too deep, duplicating `frontend/frontend/`. It was caught by
inspecting `git diff --stat` *before* merging rather than after, and the merge
itself was clean.

---

## 10. Future improvements

- **Retrieval over large log archives.** Indexing a full log store and retrieving
  only the relevant window would remove the truncation problem entirely.
- **Feedback loop on hypotheses.** Let the user mark a hypothesis confirmed or
  killed after running its test, and calibrate confidence against outcomes. Right
  now confidence is asserted and never scored.
- **Structured log parsing.** JSON and logfmt lines are treated as plain text.
  Parsing them would let the timeline group by trace id rather than message shape.
- **Semantic checking of citations.** The verifier proves a claim cites a real line;
  checking whether the claim is a *fair reading* of that line is the obvious next
  step and a much harder problem.

---

## 11. Conclusion

The habit this project changed is small and specific: we no longer accept a
technical claim from a model because it is stated without hedging. Twice — the
regex and the API key — a confident, fluent, correctly-formatted explanation was
simply false, and in both cases verification would have cost under a minute. What
made them dangerous was not that the model was wrong; it was that it did not sound
wrong.

That is also the thesis of the tool. IncidentIQ does not try to be right more
often than the model underneath it. It tries to make every claim cheap to check,
so that the reader's trust is placed in the evidence rather than in the prose.
