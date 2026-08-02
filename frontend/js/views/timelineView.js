/**
 * timelineView.js - reconstructed sequence of events.
 *
 * Two kinds of entry, drawn differently on purpose:
 *   solid dot  = observed, a timestamped line exists in the input
 *   dashed dot = inferred, someone (or something) filled in a gap
 *
 * Without that distinction a reconstructed timeline reads like a recording,
 * which is exactly the overconfidence the brief asks us to avoid.
 */

import { el, section } from "../core/dom.js";
import { registerView } from "../core/registry.js";
import { formatTs } from "../core/format.js";
import { evidenceRefs, evidenceIdSet, badge, callout, notRunYet } from "./widgets.js";

function timelineItem(item, knownIds) {
  const inferred = Boolean(item.inferred);

  return el("div", { class: `tl-item ${inferred ? "tl-item--inferred" : ""}` }, [
    el("div", { class: "tl-item__dot" }),
    el("div", { class: "tl-item__time", text: formatTs(item.timestamp) || "time unknown" }),
    el("div", { class: "tl-item__label", text: item.label }),
    item.detail && el("div", { class: "small muted", text: item.detail }),
    el("div", { class: "tl-item__foot" }, [
      inferred
        ? badge("inferred", "assumption", "No input line states this directly — it was deduced.")
        : badge("observed", "fact", "Taken straight from a timestamped input line."),
      evidenceRefs(item.evidence, knownIds),
    ]),
  ]);
}

function renderTimeline(state) {
  const { analysis } = state;
  if (!analysis) {
    return notRunYet("The timeline is built from timestamps found in the logs and alerts.");
  }

  const items = analysis.timeline || [];
  const knownIds = evidenceIdSet(analysis);

  if (!items.length) {
    return callout("warn", "!", "No timeline could be built",
      "No parseable timestamps were found. Include raw log lines with their " +
      "original time prefixes rather than a summary.");
  }

  const inferredCount = items.filter((item) => item.inferred).length;

  return el("div", { class: "stack" }, [
    inferredCount
      ? callout("warn", "~",
          `${inferredCount} of ${items.length} events are inferred, not observed`,
          "Dashed markers were deduced rather than read from a log line. Treat them " +
          "as assumptions until a source is found.")
      : callout("ok", "✓", "Every event is backed by a timestamped input line",
          "Nothing in this timeline was invented to fill a gap."),

    section("Timeline", "earliest first", el("div", { class: "card" }, [
      el("div", { class: "timeline" }, items.map((item) => timelineItem(item, knownIds))),
    ])),
  ]);
}

registerView("timeline", renderTimeline);
