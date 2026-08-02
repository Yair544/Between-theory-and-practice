# AI usage log

A running record of where AI helped during this project and where it misled us.
The brief asks for both, and the second list is the more useful one.

**Keep adding to this as you work.** Entries marked *(to fill in)* need your own
observations — copying someone else's would defeat the point of the exercise.

---

## Format

```
### YYYY-MM-DD — short title
Task:      what we asked for
Tool:      which model / interface
Outcome:   helped | misled | mixed
What happened, and what we did about it.
```

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

## To fill in as you run the tool

### (to fill in) A caught hallucination
Run the samples with a real API key and check the **Summary** tab for a red
verification banner, or the `verification.invalid_citations` field in the
response. Paste the exact citation and the claim it appeared in.

> Sample:
> Claim:
> Invented citation:
> How the tool caught it:

### (to fill in) An overconfident answer
Look for a hypothesis rated above 75% with fewer than three citations — the
overconfidence detector flags these. Record the hypothesis, its confidence, and
whether you agreed with it after reading the evidence yourself.

### (to fill in) Two models disagreeing
Run `python tools/compare_models.py <sample-id>` with both keys configured.
Record the two leading hypotheses and what the disagreement told you.

### (to fill in) A prompt change that changed the answer
Pick one of the single-variable experiments in
[`PROMPTS.md` §4.2](PROMPTS.md) and record before/after.
