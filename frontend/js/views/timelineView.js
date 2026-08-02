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
import { t } from "../core/i18n.js";
import { evidenceRefs, evidenceIdSet, badge, callout, notRunYet } from "./widgets.js";

function timelineItem(item, knownIds) {
  const inferred = Boolean(item.inferred);

  return el("div", { class: `tl-item ${inferred ? "tl-item--inferred" : ""}` }, [
    el("div", { class: "tl-item__dot" }),
    el("div", { class: "tl-item__time", text: formatTs(item.timestamp) || t("timeline.unknownTime") }),
    el("div", { class: "tl-item__label", text: item.label }),
    item.detail && el("div", { class: "small muted", text: item.detail }),
    el("div", { class: "tl-item__foot" }, [
      inferred
        ? badge(t("timeline.inferred"), "assumption", t("timeline.inferred.tip"))
        : badge(t("timeline.observed"), "fact", t("timeline.observed.tip")),
      evidenceRefs(item.evidence, knownIds),
    ]),
  ]);
}

function renderTimeline(state) {
  const { analysis } = state;
  if (!analysis) {
    return notRunYet(t("timeline.empty"));
  }

  const items = analysis.timeline || [];
  const knownIds = evidenceIdSet(analysis);

  if (!items.length) {
    return callout("warn", "!", t("timeline.none.title"), t("timeline.none.body"));
  }

  const inferredCount = items.filter((item) => item.inferred).length;

  return el("div", { class: "stack" }, [
    inferredCount
      ? callout("warn", "~",
          t("timeline.inferred.title", { count: inferredCount, total: items.length }),
          t("timeline.inferred.body"))
      : callout("ok", "✓", t("timeline.allObserved.title"), t("timeline.allObserved.body")),

    section(t("timeline.section"), t("timeline.section.hint"), el("div", { class: "card" }, [
      el("div", { class: "timeline" }, items.map((item) => timelineItem(item, knownIds))),
    ])),
  ]);
}

registerView("timeline", renderTimeline);
