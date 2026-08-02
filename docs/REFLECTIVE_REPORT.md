# IncidentIQ — Reflective Report

**Course:** Computer Science — Critical Thinking, Problem Solving and 21st-Century Skills
**Project:** IncidentIQ — an AI-powered incident response and root-cause analysis tool
**Authors:** *(to fill in — both names)*
**GitHub:** *(to fill in — repository URL)*
**Demo video:** *(to fill in — link)*
**Date:** *(to fill in)*

> **How to use this document.** Everything not marked *(to fill in)* describes the
> system as built and can be submitted as-is. The marked sections need your own
> observations from running the tool — they are the parts the brief is actually
> assessing, and they cannot be written from someone else's runs.
> Target length is 5–10 pages; the completed sections below plus your filled-in
> observations land in that range.

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
decide?** Three commitments follow from that, and they shape every part of the
system:

1. **Facts, assumptions, hypotheses and actions are kept structurally separate.**
   They are four distinct types in the schema, not four sections of one text
   field. It is not possible for the engine to return a guess in the slot where a
   fact belongs.
2. **Every AI claim must cite the specific input line it rests on**, and those
   citations are verified mechanically before a human reads them.
3. **The tool never claims a root cause.** It ranks hypotheses and attaches to
   each one a concrete test that would confirm or kill it. Confirming a cause is
   a human decision made after running that test.

---

## 2. System architecture and main features

### 2.1 Shape of the system

```
 Browser (zero-build ES modules)
     │  POST /api/analyze
     ▼
 FastAPI ─► redact ─► extract evidence ─► observed timeline
                                              │
                                              ▼
                              model pass (Gemini / Claude / GPT)
                                       │              │
                                       │              └─► offline engine
                                       ▼                   (no key, or on failure)
                                 verify citations
                                       ▼
                              challenge pass (devil's advocate)
                                       ▼
                          rule-based bias detection
                                       ▼
                          merge with the model's self-audit
                                       ▼
                          assemble + render postmortem
```

The order is fixed and each step depends on the one before it. Redaction runs
first so nothing sensitive can reach a provider. Evidence extraction runs second
so IDs exist before the model does anything. Verification runs before the
challenge pass so the devil's advocate argues against a hypothesis whose
citations are already clean. The rule-based detectors run last because several of
them read the verification result.

### 2.2 The two ideas that carry the design

**Evidence IDs assigned before the model sees anything.** A deterministic parser
splits the input into numbered items `E1..En`, keeping stack-trace continuation
lines attached to the line that started them. The model is shown those IDs and
required to cite them. Afterwards every citation is checked against the set that
actually exists. A citation to `E42` when the input stops at `E31` is a
fabrication, and it is caught by a set-membership test rather than by a reader
noticing. In the UI those broken citations render in red; in the report they are
listed individually.

This is the difference between "the AI said so" and something a reviewer can
check in five seconds — click the pill, read the line.

**Bias detection that does not depend on the model auditing itself.** Asking a
model to find bias in its own output is circular: the process that produced the
biased conclusion is the process being asked to notice it. So the eight biases
from the brief are also checked by deterministic rules that read the *shape* of
the analysis, not its prose:

| Bias / fallacy | What the rule looks at |
|---|---|
| Confirmation bias | A hypothesis with supporting evidence and an empty contradicting list |
| Anchoring bias | The leading hypothesis citing only evidence from the first fifth of the input |
| Post hoc fallacy | A deploy-blaming hypothesis whose only citations are deployment notes — no log line links the deploy to the failure |
| Overconfidence bias | Stated confidence ≥ 0.75 on fewer than three citations |
| Availability bias | A stock cause ("memory leak", "DNS") that appears nowhere in the input |
| Base-rate neglect | A log pattern repeating five or more times that no hypothesis mentions |
| Hindsight bias | "Obviously", "clearly", "as expected" applied to a cause nobody knew at the time |
| Automation bias | A confident leading hypothesis in a run that failed the grounding check |

Where a rule and the model flag the same bias, the finding is labelled
*rule + model* — the strongest signal the tool produces. Automation bias is the
odd one out and is documented as such in `biases.py`: it lives in the reader, not
in the text, so the rule can only flag the *shape* that invites it.

### 2.3 Features against the brief's requirements

| Required feature | How it is met |
|---|---|
| Input interface | Six separate fields (description, logs, traces, alerts, deploy notes, user reports), paste or file upload, plus three bundled sample incidents |
| AI-powered incident summary | Structured summary with citations; verification banner shown *above* it |
| Timeline reconstruction | Deterministic timeline from parsed timestamps, marked *observed*; model-added events marked *inferred* and drawn with dashed markers |
| Root-cause hypothesis generator | N competing hypotheses (default 4), each with confidence, evidence for, evidence against, and a recommended test |
| Bias and fallacy detector | All eight from the brief, checked by rules and by the model, merged |
| Suggested next actions | Prioritised, each citing the evidence that motivates it; ungrounded ones are explicitly marked "generic advice" |
| Draft postmortem | Markdown export with the verification numbers included, not buried |

Beyond the basic scope: file upload, evidence-source filtering, confidence
ranking, evidence for/against tables, role-based rewrites (engineer / manager /
support), unsupported-claim detection, a devil's-advocate pass, PII redaction, an
offline mode, a cross-model comparison tool, and a full Hebrew interface with
right-to-left layout.

**On the Hebrew mode**, one decision is worth recording because it follows from
the same principle as the rest of the tool. The interface and the model's prose
are translated; the evidence is not. A log line quoted back in Hebrew is no
longer a quotation — it cannot be matched against the input, so the verifier
could not check it and the citation would become decorative. Machine text
(log lines, stack traces, timestamps, evidence ids) therefore stays in its
original wording and left-to-right direction even when everything around it is
Hebrew. The offline engine is translated too: it runs whenever a model call
fails, and on a free-tier key that happens often enough that a Hebrew user meets
it in normal use rather than as an edge case.

---

## 3. Technologies used

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.10+, FastAPI, Pydantic v2 | Typed schemas that double as validation and as the API contract |
| Frontend | HTML + CSS + native ES modules, **no build step** | The tool has to start with one double-click on a machine we do not control. A `npm install` in that path is a way for the demo to fail |
| AI | Google Gemini (`gemini-2.5-flash`) primary; Claude and GPT selectable | Behind a provider interface; nothing above it imports a vendor SDK, so switching model is one line in `.env` |
| Config | `python-dotenv` | Keys live in `.env`, never in git |
| Tests | pytest — 73 tests | None call a model |

**A note on the frontend choice.** React would have been faster to write. It
would also have meant a build step, `node_modules`, and a version of the app that
can be stale relative to the backend. For a tool whose grading path is "double
click `run.bat`", plain modules were the more defensible engineering decision.
The cost is about 200 lines of DOM helpers in `core/dom.js`.

---

## 4. How AI was used

### 4.1 Inside the product

Three calls, all defined in `backend/services/prompts.py`:

1. **The analysis pass.** One structured call producing the whole investigation
   against a JSON schema.
2. **The challenge pass.** A *separate* call with a fresh context, told it is a
   skeptical reviewer with no stake in the analysis, asked to argue the leading
   hypothesis is wrong. This is deliberately not a follow-up turn: a model asked
   "now criticise yourself" is still completing its own train of thought and
   tends to produce a polite critique that concedes the point.
3. **Audience rewrites.** Part of the analysis schema rather than a third call,
   so the same structured facts produce all three versions and the manager
   version cannot quietly acquire certainty the engineer version lacks.

The system prompt is built around seven rules, each aimed at a specific failure
mode. Full text and rationale: [`PROMPTS.md`](PROMPTS.md).

### 4.2 Prompt iterations

Four changes made during development, each after observing a failure:

| Symptom observed | Change | Effect |
|---|---|---|
| `contradicting_evidence` empty on nearly every hypothesis | Rule 4 rewritten to "An empty contradicting list is a **claim that you looked**" | The field became an assertion rather than an omission |
| Confidence clustered at 0.85–0.95, no discrimination | Rule 5 capped confidence at 0.75 unless independent evidence agrees | Spread restored; the number started meaning something |
| Four or five generic biases reported every run | Rule 6 gained "reporting none is acceptable and preferable to inventing one" | Bias-theatre stopped |
| On `checkout-v241`, all four hypotheses blamed release v2.4.1 | Rule 3 gained "at least one hypothesis must NOT blame the most recent deployment" | Four variations on one answer became four hypotheses |

The last one is the interesting case: the sample is *designed* to bait post hoc
reasoning, the model took the bait, and the fix was a prompt constraint rather
than better model output.

### 4.3 During development

Documented in [`AI_USAGE_LOG.md`](AI_USAGE_LOG.md), including two failures worth
summarising here.

**A regex that was described correctly and behaved wrongly.** Three modules each
needed to group repeated log lines, and each got its own generated copy of a
normalising helper. The regex was supposed to blank digits so that two timeouts
one minute apart collapsed into one event. It did not: `\b\d+\b` does not match
`02Z`, because there is no word boundary between a digit and a letter, so the
seconds field survived and every line stayed unique. The code *read* correctly,
review passed it, and the bug only surfaced when a 59-line sample produced 39
"distinct" timeline events that were visibly repeats. Fixed by consolidating into
`textutil.py` with a test asserting exactly the two-line case.

**A circular import that "should be fine".** Asked whether views importing
`registerView` from `app.js` while `app.js` imported the views was safe, the model
explained — correctly — that ES modules hoist function declarations. It was wrong
about *this* code, where the function closed over a `const` that was still in the
temporal dead zone. The general shape of that failure is the dangerous one: an
answer that is right about the mechanism and wrong about the case, which a
follow-up question will not catch because the follow-up gets the same
correct-in-general answer.

### 4.4 *(to fill in)* Examples of useful AI output

Run the samples with a key and paste two or three genuinely good outputs — a
hypothesis you would not have thought of, a rebuttal that changed your mind, a
timeline inference that turned out to be right.

### 4.5 *(to fill in)* Examples of incorrect, misleading, hallucinated or overconfident output

The tool records these for you. Check `verification.invalid_citations` after each
run, and look for hypotheses the overconfidence detector flagged. Paste them
verbatim — an invented citation is the single clearest demonstration of the point
this project is about.

---

## 5. How we tested and challenged the AI

| Method the brief asks for | How we did it |
|---|---|
| Check whether each AI claim is supported by the input | Automated: `verifier.py` checks every citation against the evidence set on every run |
| Compare multiple prompts or models | `tools/compare_models.py` runs identical input through every provider that has a key configured (Gemini, Claude, GPT) and diffs the leading hypothesis, citation overlap and grounding score |
| Ask the AI to argue against its own conclusion | Built into the product as the devil's-advocate pass |
| Test whether small prompt changes produce different answers | Single-variable experiments, procedure in [`PROMPTS.md` §4.2](PROMPTS.md) |
| Record examples of hallucination and overconfidence | Every response carries a `verification` block; the overconfidence rule flags high-confidence/low-evidence hypotheses |
| Document where AI helped and where it misled | [`AI_USAGE_LOG.md`](AI_USAGE_LOG.md) |

**The control condition.** The offline engine is not a stub — it is a real
analysis with no model involved. Running the same incident with and without a key
isolates what the AI actually contributed. *(to fill in: do this on one sample and
record the difference. Our expectation is that the offline engine finds the error
clusters and the model supplies the causal reasoning and the disconfirming
evidence — check whether that holds.)*

---

## 6. Problems encountered and how they were solved

| Problem | Solution |
|---|---|
| Models cite evidence that does not exist | IDs assigned deterministically before the model runs; every citation set-checked afterwards; invented ones shown in red and listed in the report |
| Models return prose around the JSON, or get cut off mid-object | Structured output requested from both providers, plus tolerant recovery that reports every repair as a warning — a silent repair is how you stop noticing a broken prompt |
| A model asked to self-audit for bias finds bias everywhere, or nowhere | Independent deterministic rules; the two results are merged and agreement is labelled |
| The tool must be gradeable without an API key | Offline engine, clearly labelled everywhere, with the launcher explaining what will and will not work |
| Confidence scores are meaningless by default | Capped in the prompt, banded in the UI, and the top band is "well supported" — never "confirmed" |
| Duplicated normalisation logic drifted and broke grouping | Consolidated into `textutil.py` with a regression test |
| Sending production logs to a third party | Redaction before any provider call, on by default, with the count surfaced in the UI so the user knows it happened |

*(to fill in: add the problems you hit that are not on this list — environment
setup, merge conflicts, disagreements about scope. Those are part of the honest
account.)*

---

## 7. Cognitive biases and fallacies encountered

The brief asks for at least three; strong reports discuss five or more. All eight
from the brief are implemented as detectors — but implementing a detector is not
the same as *encountering* the bias, and this section should be about the second
thing.

Below, the three we can document from building the tool. **Fill in at least two
more from running it.**

### Post hoc fallacy — encountered in the tool's output
Where it appeared: on the `checkout-v241` sample, early runs produced four
hypotheses and all four blamed release v2.4.1, deployed twelve minutes before the
first error. The sample is built so this is wrong: the latency alert fires
*fifteen minutes before* the deploy, and a partner using the same payment provider
reports the same slowness. The deploy shrank a safety margin; it did not create
the problem.
How we noticed: reading the evidence ourselves and finding the 09:47 alert.
How we reduced it: rule 3 in the system prompt now requires at least one
hypothesis that does not involve the most recent change, and a deterministic
detector flags any deploy-blaming hypothesis whose only support is deployment
notes.

### Automation bias — encountered in ourselves, during development
Where it appeared: the generated normalisation helper described in §4.3. It was
accepted because it looked like the kind of code that works, and the explanation
attached to it was fluent and correct-sounding.
How we noticed: a sample produced 39 timeline events that were obviously the same
message repeated.
How we reduced it: a regression test for exactly the two-line case, and a
standing rule that generated regexes get a test before they get a review.
This is also why the tool raises automation bias as a *risk* whenever a confident
answer coexists with a failed grounding check — the fluency is the danger.

### Overconfidence bias — encountered in the tool's output
Where it appeared: before the confidence cap, hypotheses came back at 0.85–0.95
regardless of how much evidence supported them.
How we noticed: the scores stopped discriminating — everything was "very likely",
so the ranking carried no information.
How we reduced it: an explicit ceiling in the prompt, a detector that flags high
confidence on thin citations, and a UI that never uses the word "confirmed".

### *(to fill in)* Confirmation bias
Look for a run where a hypothesis had supporting evidence and an empty
contradicting list. Did you notice before the tool told you?

### *(to fill in)* Anchoring, availability, hindsight or base-rate neglect
Pick at least one more from your own runs. For each: where it appeared, how it
affected your thinking, how you noticed, and how you reduced its effect.

---

## 8. Ethical and professional risks

**What could go wrong if engineers trust the tool too much.** The realistic
failure is not a wildly wrong answer — those get caught. It is a *plausible* wrong
answer delivered with citations, which sends a team down a three-hour path while
the real cause keeps hurting users. The tool's mitigations are structural: it
never presents one answer, it shows evidence against as prominently as evidence
for, and it attaches a falsifying test to every hypothesis. None of that stops a
tired engineer at 3am from reading only the top card.

**Should the tool ever claim it found the root cause?** No, and it does not. A
root cause is confirmed by an experiment, not by an argument. The strongest label
in the UI is "well supported"; the report header says DRAFT and states that the
cause has not been confirmed.

**How uncertainty is shown.** Deliberately, in more than one channel, because a
single signal gets tuned out: a numeric confidence *and* a band, distinct visual
treatment for facts versus assumptions, dashed markers for inferred timeline
events, an explicit warning when a hypothesis has no contradicting evidence, and
a grounding percentage in the status bar at all times.

**What should not be sent to an external AI API.** Production logs routinely
contain user emails, IP addresses, session tokens, and sometimes payment data.
`redaction.py` strips values with a recognisable shape before any provider call,
on by default, and the UI reports how many were removed. Its limits are stated in
the module docstring: it is pattern matching, so it catches an email and misses
"customer 88213 requested deletion". For genuinely sensitive systems the honest
answer is a local model or no model.

We also learned this one the hard way rather than in the abstract. Midway through
the project one of us pasted an API credential directly into an AI chat window to
speed up configuration — having already written the module whose entire job is
stopping secrets from reaching a third party. The key was revoked and reissued,
and the incident is written up in [`AI_USAGE_LOG.md`](AI_USAGE_LOG.md). The
lesson generalises past our own carelessness: **the safeguards a tool enforces do
not automatically govern the people operating it.** A redaction pass that runs on
`POST /api/analyze` says nothing about what a tired engineer pastes into a chat
at 2am, and an incident-response tool is used mostly by tired engineers. It is
the same automation-bias failure in a different costume — trusting that because
the system handles it, we do not have to.

**Who is responsible if the AI recommends a harmful action.** The person who runs
the command. That is not a disclaimer — it is a design constraint, and it is why
the actions pane warns before destructive steps that a restart both fixes the
problem and destroys the evidence, and why no action in this tool is executable
from the tool.

**How the tool supports human judgement instead of replacing it.** By being
auditable rather than authoritative: every claim is one click from the line it
came from, the reasoning-risks pane is about how *this investigation* may be
going wrong, and the verification banner appears above the summary rather than in
a footnote. A reader who checks nothing still sees how much was checked for them.

---

## 9. Division of work

*(to fill in — required for pair submissions.)*

Suggested structure:

| Area | Partner A | Partner B |
|---|---|---|
| Frontend (design system, views) | | |
| Backend (evidence, timeline, redaction) | | |
| Prompt design and iteration | | |
| Verification and bias detectors | | |
| Sample incidents | | |
| Tests | | |
| Documentation and report | | |
| Demo video | | |

Add a paragraph on how you worked together — how you split it, what you reviewed
for each other, and any disagreement you had to resolve. Reviewing each other's
prompt changes is worth mentioning if you did it: prompts are the part of this
codebase most likely to be changed carelessly, because a prompt edit never fails
to compile.

---

## 10. Future improvements

- **Retrieval over large log archives.** The current cap is per-analysis text.
  Indexing a full log store and retrieving only the relevant window would remove
  the truncation problem entirely.
- **Feedback loop on hypotheses.** Let the user mark a hypothesis confirmed or
  killed after running its test, and use the accumulated record to calibrate
  confidence against outcomes. Right now confidence is asserted and never scored.
- **Structured log parsing.** JSON and logfmt lines are currently treated as
  plain text. Parsing them would let the timeline group by trace id rather than
  by message shape, which is the correct grouping.
- **A local model option.** For environments where sending logs to a third party
  is not acceptable at all, redaction is a mitigation rather than an answer.
- **Semantic checking of citations.** The verifier proves a claim cites a real
  line. Checking whether the claim is a fair reading of that line is the obvious
  next step and a much harder problem.
- **Detecting contradictions between evidence items.** Two log lines that cannot
  both be true is a strong signal, and nothing currently looks for it.

---

## 11. Conclusion

*(to fill in — a short honest paragraph. What did building this change about how
you use AI? The most useful version of this answer is specific: name a habit you
had before and what you do differently now.)*
