/**
 * actionsView.js - recommended next debugging steps.
 *
 * The brief asks for steps "linked to evidence, not generic advice", so an
 * action with no citations is shown as a warning rather than quietly listed
 * next to the grounded ones.
 */

import { el, section } from "../core/dom.js";
import { registerView } from "../core/registry.js";
import { priorityTone } from "../core/format.js";
import { evidenceRefs, evidenceIdSet, badge, callout, notRunYet } from "./widgets.js";

const PRIORITY_ORDER = { P1: 0, P2: 1, P3: 2, P4: 3 };

const OWNER_LABEL = {
  engineer: "on-call engineer",
  sre: "SRE / platform",
  manager: "engineering manager",
  support: "support team",
  security: "security",
};

function actionRow(action, index, knownIds) {
  const grounded = Boolean(action.evidence?.length);

  return el("tr", {}, [
    el("td", {}, [badge(action.priority || "P3", priorityTone(action.priority))]),
    el("td", {}, [
      el("div", { style: { fontWeight: "550" }, text: action.action }),
      action.rationale && el("div", { class: "xsmall faint", text: action.rationale }),
      !grounded
        ? el("div", { class: "xsmall", style: { color: "var(--c-unsupported)" } }, [
            "generic advice — no evidence in this incident motivates it",
          ])
        : null,
    ]),
    el("td", { class: "nowrap" }, [
      el("span", { class: "xsmall", text: OWNER_LABEL[action.owner_role] || action.owner_role || "—" }),
    ]),
    el("td", {}, [evidenceRefs(action.evidence, knownIds, { emptyLabel: "ungrounded" })]),
  ]);
}

function renderActions(state) {
  const { analysis } = state;
  if (!analysis) {
    return notRunYet("Recommended debugging steps appear here once an analysis has run.");
  }

  const actions = [...(analysis.next_actions || [])].sort(
    (a, b) => (PRIORITY_ORDER[a.priority] ?? 9) - (PRIORITY_ORDER[b.priority] ?? 9)
  );
  const knownIds = evidenceIdSet(analysis);

  if (!actions.length) {
    return callout("warn", "!", "No next actions produced",
      "Nothing actionable could be derived from the current evidence.");
  }

  const ungrounded = actions.filter((action) => !action.evidence?.length).length;

  return el("div", { class: "stack" }, [
    ungrounded
      ? callout("warn", "!", `${ungrounded} of ${actions.length} steps are generic`,
          "They are not wrong, but nothing in this incident specifically points to them. " +
          "Do the evidence-backed steps first.")
      : callout("ok", "✓", "Every step is tied to specific evidence",
          "Each row cites the input that motivates it."),

    section("Next debugging steps", "highest priority first",
      el("div", { class: "card card--flush" }, [
        el("div", { class: "table-wrap" }, [
          el("table", { class: "table" }, [
            el("thead", {}, [
              el("tr", {}, [
                el("th", { text: "Pri" }),
                el("th", { text: "Action" }),
                el("th", { text: "Owner" }),
                el("th", { text: "Because of" }),
              ]),
            ]),
            el("tbody", {}, actions.map((action, index) => actionRow(action, index, knownIds))),
          ]),
        ]),
      ])),

    callout("info", "i", "Before you run anything destructive",
      "A restart or a rollback both fixes and destroys evidence. If the incident is " +
      "not actively hurting users, capture the current state first — the next hour of " +
      "investigation depends on it."),
  ]);
}

registerView("actions", renderActions);
