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
import { t } from "../core/i18n.js";
import { evidenceRefs, evidenceIdSet, badge, callout, notRunYet } from "./widgets.js";

const PRIORITY_ORDER = { P1: 0, P2: 1, P3: 2, P4: 3 };

/** Owner roles resolve through `owner.<role>` keys, falling back to the raw
 *  value so a role the backend invents still renders as something. */
function ownerLabel(role) {
  const key = `owner.${role}`;
  const label = t(key);
  return label === key ? role || "—" : label;
}

function actionRow(action, index, knownIds) {
  const grounded = Boolean(action.evidence?.length);

  return el("tr", {}, [
    el("td", {}, [badge(action.priority || "P3", priorityTone(action.priority))]),
    el("td", {}, [
      el("div", { style: { fontWeight: "550" }, text: action.action }),
      action.rationale && el("div", { class: "xsmall faint", text: action.rationale }),
      !grounded
        ? el("div", { class: "xsmall", style: { color: "var(--c-unsupported)" } }, [
            t("actions.genericNote"),
          ])
        : null,
    ]),
    el("td", { class: "nowrap" }, [
      el("span", { class: "xsmall", text: ownerLabel(action.owner_role) }),
    ]),
    el("td", {}, [evidenceRefs(action.evidence, knownIds, { emptyLabel: t("actions.ungrounded") })]),
  ]);
}

function renderActions(state) {
  const { analysis } = state;
  if (!analysis) {
    return notRunYet(t("actions.empty"));
  }

  const actions = [...(analysis.next_actions || [])].sort(
    (a, b) => (PRIORITY_ORDER[a.priority] ?? 9) - (PRIORITY_ORDER[b.priority] ?? 9)
  );
  const knownIds = evidenceIdSet(analysis);

  if (!actions.length) {
    return callout("warn", "!", t("actions.none.title"), t("actions.none.body"));
  }

  const ungrounded = actions.filter((action) => !action.evidence?.length).length;

  return el("div", { class: "stack" }, [
    ungrounded
      ? callout("warn", "!",
          t("actions.generic.title", { count: ungrounded, total: actions.length }),
          t("actions.generic.body"))
      : callout("ok", "✓", t("actions.grounded.title"), t("actions.grounded.body")),

    section(t("actions.section"), t("actions.section.hint"),
      el("div", { class: "card card--flush" }, [
        el("div", { class: "table-wrap" }, [
          el("table", { class: "table" }, [
            el("thead", {}, [
              el("tr", {}, [
                el("th", { text: t("actions.col.priority") }),
                el("th", { text: t("actions.col.action") }),
                el("th", { text: t("actions.col.owner") }),
                el("th", { text: t("actions.col.because") }),
              ]),
            ]),
            el("tbody", {}, actions.map((action, index) => actionRow(action, index, knownIds))),
          ]),
        ]),
      ])),

    callout("info", "i", t("actions.warn.title"), t("actions.warn.body")),
  ]);
}

registerView("actions", renderActions);
