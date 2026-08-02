# Example incidents

Each file here is one incident. Drop a new `.json` in this folder and it appears
in the sidebar on the next page load — no code change needed.

## Format

```jsonc
{
  "id": "unique-slug",          // required
  "title": "Short title",       // required
  "scenario": "Domain · hint",  // shown under the title in the sidebar
  "description": "...",         // maps to the "Incident description" field
  "logs": "...",
  "errors": "...",
  "alerts": "...",
  "deploy_notes": "...",
  "user_reports": "..."
}
```

## Why these three

They are not random. Each one is built to exercise a different failure mode of
AI-assisted investigation, so the reasoning-risks pane has something real to
find. The synthetic data was generated with AI and then hand-edited — mostly to
*remove* the tidiness that made the first drafts too easy.

| Sample | The trap it sets |
|---|---|
| `checkout-v241` | **Post hoc.** A deployment 12 minutes before the first error is the obvious suspect, and it is genuinely involved — but the latency alert fires *15 minutes before the deploy*, and a partner using the same payment provider reports the same slowness. The deploy shrank the safety margin; it did not create the problem. An analysis that stops at "v2.4.1 broke checkout" has stopped one step early. |
| `registration-peak` | **Availability bias and base-rate neglect.** There is no deployment to blame, which pushes a model toward stock answers ("memory leak", "DDoS"). The actual lead is a cost-reduction database resize six days earlier, justified by *average* CPU — a base-rate error made by the humans, visible only in the deployment notes. |
| `booking-intermittent-500` | **Overconfidence on thin evidence.** Sixteen log lines, one error type, and an intermittent symptom. The config was applied without restarting pods, so only some of them picked it up — which explains "one request in six" and "terminal 3 seems worse". A confident single root cause here is a bug in the analysis, not a finding. |

None of the three has its answer written down anywhere in the repository. That
is deliberate: the point of the exercise is to check whether the tool's
reasoning survives contact with evidence that does not spell out the conclusion.
