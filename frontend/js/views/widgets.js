/**
 * widgets.js - small building blocks shared by the analysis views.
 *
 * The evidence-reference pill is the most important thing in this file. Every
 * claim the system makes carries the IDs of the evidence it rests on, and
 * clicking a pill jumps to that exact line. That is what turns "the AI said
 * so" into something a reviewer can check.
 */

import { el, qs } from "../core/dom.js";
import { setState } from "../core/store.js";
import { pct, confidenceBand, severityTone } from "../core/format.js";
import { t } from "../core/i18n.js";

/** Jump to the Evidence tab and flash the referenced line. */
function focusEvidence(evidenceId) {
  setState({ activeTab: "evidence" });
  // The pane is rebuilt by the store subscription, so wait a frame.
  requestAnimationFrame(() => {
    const node = qs(`#ev-${CSS.escape(evidenceId)}`);
    if (!node) return;
    node.scrollIntoView({ behavior: "smooth", block: "center" });
    node.classList.remove("is-highlighted");
    void node.offsetWidth; // restart the animation
    node.classList.add("is-highlighted");
  });
}

/**
 * Render one citation.
 * @param {string} id e.g. "E7"
 * @param {Set<string>} knownIds ids that actually exist in the evidence list
 */
export function evidenceRef(id, knownIds) {
  const exists = !knownIds || knownIds.has(id);
  if (!exists) {
    return el("span", {
      class: "evref evref--broken",
      title: t("evref.broken.title", { id }),
      text: id,
    });
  }
  return el("button", {
    class: "evref",
    type: "button",
    title: t("evref.show"),
    onClick: () => focusEvidence(id),
  }, [id]);
}

/** Render a list of citations, or an explicit "no evidence cited" marker. */
export function evidenceRefs(ids, knownIds, { emptyLabel } = {}) {
  const list = Array.isArray(ids) ? ids : [];
  if (!list.length) {
    return el("span", {
      class: "badge badge--unsupported",
      title: "This statement is not backed by any input evidence.",
      text: emptyLabel || t("empty.noEvidence"),
    });
  }
  return el("span", { class: "evref-list" }, list.map((id) => evidenceRef(id, knownIds)));
}

/** A labelled confidence bar. */
export function confidenceMeter(value) {
  const band = confidenceBand(value);
  const width = Math.max(0, Math.min(1, value ?? 0)) * 100;
  return el("div", { class: "meter", title: `${band.label} (${pct(value)})` }, [
    el("div", { class: "meter__track" }, [
      el("div", { class: `meter__fill meter__fill--${band.tone}`, style: { width: `${width}%` } }),
    ]),
    el("span", { class: "meter__value", text: pct(value) }),
  ]);
}

/** Generic badge. */
export function badge(text, tone = "info", title) {
  return el("span", { class: `badge badge--${tone}`, title, text });
}

/** Badge whose tone follows a severity string. */
export function severityBadge(severity) {
  return badge(severity || "info", severityTone(severity));
}

/** Callout box used for warnings and framing notes. */
export function callout(tone, icon, title, body) {
  return el("div", { class: `callout callout--${tone}` }, [
    el("span", { class: "callout__icon", text: icon }),
    el("div", { class: "callout__body" }, [
      title && el("div", { class: "callout__title", text: title }),
      typeof body === "string" ? el("div", { text: body }) : body,
    ]),
  ]);
}

/** Build the lookup used to detect fabricated citations. */
export function evidenceIdSet(analysis) {
  return new Set((analysis?.evidence || []).map((item) => item.id));
}

/** Shown in every pane before the first analysis is run. */
export function notRunYet(text) {
  return el("div", { class: "empty" }, [
    el("div", { class: "empty__icon", text: "○" }),
    el("div", { class: "empty__title", text: t("empty.notRun") }),
    el("div", { class: "empty__text", text }),
  ]);
}
