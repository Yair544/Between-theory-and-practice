# AI usage log

A running record of where AI helped during this project and where it misled us.
The brief asks for both, and the second list is the more useful one.

Entries are grouped by what the AI did to us rather than by date: where it
helped, where it misled us, and what we observed running the finished tool.
Each one states its outcome and what we changed as a result.

The last group matters most. It records what the tool actually did on real runs,
including the places where the expected failure did not occur — reporting "no
hallucination appeared" is more useful than hunting until one does.

---

## Where AI helped

### Generating the synthetic incident data
**Task:** Produce three realistic incident datasets with logs, alerts, traces and
support tickets.
**Tool:** Claude (chat)
**Outcome:** helped

Writing 150 lines of plausible production logs by hand is slow and the result
tends to be too clean. AI produced usable drafts in minutes. The drafts still
needed hand-editing, and almost all the edits went one direction: putting the
*mess* back in. The first versions had every error neatly explaining itself, no
red herrings, and a timeline where cause visibly preceded effect. That would have
made the tool look far better than it is, because the hard part of incident
analysis is exactly the noise the model had smoothed away. See
[`data/samples/README.md`](../data/samples/README.md) for what each sample is now
designed to trap.

### Rewriting the reasoning-risk explanations
**Task:** Turn terse bias definitions into text an on-call engineer would read at
2am.
**Tool:** Claude
**Outcome:** helped

Useful for tone. Every claim about *what the detector actually does* still had to
be checked against the code, because the model happily wrote confident
descriptions of capabilities the detector did not have.

### Boilerplate and scaffolding
**Task:** Pydantic schemas, FastAPI routing, CSS token structure.
**Tool:** Claude
**Outcome:** helped

Fast and mostly correct. This is the category where AI assistance is least
interesting and most reliable.

---

## Where AI misled us

### Confidently wrong about its own regex
**Outcome:** misled

Three modules independently needed to group repeated log lines, and each ended up
with its own copy of a `_shape()` helper that blanked numbers so that

```
10:15:02Z ERROR pool timed out after 30000ms
10:19:44Z ERROR pool timed out after 45000ms
```

would collapse into one event. The generated regex was described as handling
this, and it looked plausible. It did not: `\b\d+\b` does not match `02Z`,
because there is no word boundary between a digit and a letter, so the seconds
field survived normalisation and **every line stayed unique**. The bug was
invisible in review — the code reads correctly — and only showed up when the
timeline for a 59-line sample came back with 39 "distinct" events that were
obviously repeats.

Two lessons, both of which the brief predicts:

1. *Automation bias.* The helper was accepted because it looked like the kind of
   thing that works. Nobody ran it against two lines that differed only in the
   timestamp until much later.
2. Duplicated logic drifts. The fix (`backend/services/textutil.py`) puts one
   implementation behind one name, with a test that asserts exactly the two-line
   case above.

### A circular import that "should be fine"
**Outcome:** misled

The first frontend design had each view import `registerView` from `app.js` while
`app.js` imported the views. Asked whether this was safe, the model said ES
modules handle circular imports through hoisting — which is true for function
declarations and false for the `const views = {}` the function closed over. The
first view to evaluate hit a temporal dead zone. Fixed by extracting
`core/registry.js`.

The general shape is worth noting: the answer was *correct about the mechanism*
and *wrong about this code*. That is the failure mode hardest to catch by asking
a follow-up question, because the follow-up gets the same correct-in-general
answer.

### We leaked our own API key into a chat window
**Outcome:** misled — by ourselves, not by the model

While switching the project to Gemini, one of us pasted an API credential
straight into an AI chat to "just set it up". Nothing catastrophic followed — the
key was revoked and reissued — but it is worth writing down, because this project
is *about* being careful with what leaves your machine and we did the exact thing
`redaction.py` exists to prevent.

Three things this made concrete:

1. **A chat window is a third party.** We had already written a module that
   strips keys out of logs before they reach a provider, and then hand-carried
   one to a provider ourselves. The tool's discipline did not transfer to the
   humans using it.
2. **Revocation is the only real remedy.** Once a secret is in a transcript you
   cannot un-send it. "It was probably fine" is not a control.
What changed as a result: `gemini_client.py` now detects the "API key not valid"
response and reports it clearly instead of surfacing a bare HTTP 400.

### The AI told us our valid API key was invalid
**Outcome:** misled — and the most instructive failure in the project

Immediately after the incident above, the assistant helping us build this told
us — twice, confidently, unprompted — that our key was the wrong *kind* of
credential: that Gemini API keys begin `AIza`, and that a key beginning `AQ.`
was an OAuth access token which "will not work here". It went further and wrote
that claim into the product: into the error message in `gemini_client.py`, into
the comment in `.env.example`, and into the README.

All of it was wrong. Google issues API keys in more than one format, and `AQ.`
keys are current and valid. A one-line smoke test against the real API returned
`OK` on the first try.

Why this is the entry worth reading:

- **It was not a hedge, it was an assertion.** The tone carried no uncertainty,
  which is exactly why we believed it. We deleted a working key and generated a
  second one on that advice, and the second key had the same prefix — which
  should have been the tell, and was not, because we were still trusting the
  explanation over the evidence in front of us.
- **The wrong claim propagated into the code.** It was not a passing remark in
  a chat; it became a validation message that would have told *future users* the
  same falsehood. Bad AI output is most dangerous when it gets committed.
- **Verification took thirty seconds.** One API call settles it. We reached for
  it only after the second key looked identical to the first.

This is textbook **automation bias** — the same failure `biases.py` describes and
the tool flags in its own output — and we walked into it while building the tool
that flags it. The claim was specific, technical, and delivered fluently, which
is the exact profile the reasoning-risks pane warns about.

The corrected code now refuses to assert which prefix is legitimate. It reports
what Google actually said and links to the console, because the API is the
authority on what the API accepts. The comment in `gemini_client.py` records why
that restraint is there, so nobody helpfully "improves" it back.

### Hedging that looked like analysis
**Outcome:** mixed

Early prompt drafts produced summaries full of "it is possible that there may be
an issue with". Fluent, professional, and containing no information. The system
prompt now bans that pattern explicitly, and `report.py` prints the verification
numbers rather than describing them in prose.

---

## Observations from running the tool

The reference run for this section is saved verbatim as
[`data/samples/example-output.md`](../data/samples/example-output.md):
`checkout-v241` through `gemini-2.5-flash`, 59 evidence items, 29 checkable
claims, grounding 100%.

### No hallucination in the recorded runs — and that is a finding, not a pass

The honest result: **zero invented citations**. Every one of the 29 checkable
claims cited an evidence ID that exists, so `verification.invalid_citations` came
back empty and the red banner never appeared.

That is worth stating plainly rather than hunting until we found a failure. It
does not mean the model cannot fabricate — it means that on this input, with IDs
supplied in the prompt and a schema constraining the output, it did not. What the
run does demonstrate is that the check is real and cheap: 29 claims verified
mechanically against a set of 59 IDs, with the score printed above the summary
instead of buried.

The claim the verifier *cannot* make is the interesting one. Grounding measures
traceability, not correctness — a citation can point at a real line and still
misread it. Hypothesis 1 cites `[E1, E4, E5 … E56]`, 25 IDs, all valid. Nothing
in the 100% score says the causal story built on them is right.

### An overconfident answer — with a twist we did not expect

Hypothesis 1 came back at **75%**, exactly the ceiling rule 5 imposes, and the
overconfidence detector did **not** fire — it looks for high confidence on fewer
than three citations, and this had 25.

What fired instead was **confirmation bias**, and reading the card shows why:

> Evidence for: 25 IDs
> Evidence against: *(none found — note that this may mean nobody looked)*

So the number was not unearned, it was *one-sided*. The model searched hard in
one direction and reported the result of that search as a property of the world.
A detector tuned only to "confident but thinly cited" would have called this
hypothesis exemplary. The shape that gave it away was the empty column, not the
score — which is the argument for having several rules read different things.

For contrast, the other three hypotheses in the same run carried real
disconfirming evidence (60% with 5 for / 8 against; 50% with 8 for / 2 against;
20% with 3 for / 7 against). The spread is what the confidence cap was added to
restore, and here it held.

The devil's-advocate pass then did the job the leading hypothesis had skipped: it
found that H1 cannot explain E57, the customer charged twice, since a
connection merely consumed for five seconds and failed should not produce a
charge. That rebuttal came from a separate call with a fresh context, and it
attacked the analysis the main pass had been satisfied with.

### Two engines disagreeing on the same incident

We could not run the two-LLM comparison: only a Gemini key was configured, so
`tools/compare_models.py` had nothing to compare against. What we ran instead was
the control condition — the same incident with the model removed entirely — and
the contrast is sharper than a model-versus-model diff would have been.

| | Offline engine | gemini-2.5-flash |
|---|---|---|
| Leading "hypothesis" | *"The failure is centred on: ERROR HikariPool-payment connection is not available…"* | *"v2.4.1's pooled client and retry logic exhaust connections under rising upstream gateway latency"* |
| Top confidence | 0.32 | 0.75 |
| Disconfirming evidence | none on any hypothesis | on three of four |
| Counter-argument | — | identifies the E57 double-charge the leader cannot explain |

The offline engine finds *where* the errors cluster. It never proposes a
mechanism, never links the deploy to the pool, and never argues with itself — its
"hypotheses" are error-shape groupings with the numbers blanked. That is the
honest boundary of what the deterministic layer contributes, and it is exactly
the part the AI supplies: causal structure and disconfirmation.

It also means the offline banner is not a cosmetic degradation. A user who sees
it is getting a genuinely weaker analysis, which is why it is labelled loudly.

### A prompt change that changed the answer

Documented during development, from `checkout-v241`. Before the change, all four
hypotheses blamed release v2.4.1 — four rewordings of one answer. The sample is
built so that this is wrong: the latency alert fires fifteen minutes *before* the
deploy.

Adding one line to rule 3 — *"At least one hypothesis must NOT blame the most
recent deployment or config change"* — produced the run recorded above, where
hypothesis 2 is external gateway degradation and hypothesis 4 is internal
resource contention. The summary now opens by noting that gateway latency was
already climbing before the release.

One sentence of prompt moved the output from a post hoc pile-on to a genuine
differential. That is the uncomfortable part: the model had the contradicting
evidence in front of it the whole time and cited it once asked, so the failure
was never a knowledge gap — it was that nothing had required it to look.

### The free tier runs out, and the fallback is not hypothetical

While collecting the runs above, the Gemini free-tier quota was exhausted and
every subsequent call returned a rate-limit error. The pipeline degraded to the
offline engine exactly as designed, labelled it, and returned an analysis rather
than an error page.

Two things follow. The offline path is a normal operating mode on a free key, not
an edge case — which is why it is translated into Hebrew as well. And a test that
quietly depended on a live API call failed for a reason that had nothing to do
with what it was testing; see the note in `tests/conftest.py`.
