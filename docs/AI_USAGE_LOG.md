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
