/**
 * risksView.js - the reasoning-risks report.
 *
 * The bias list is not invented by us: it is the eight biases and fallacies
 * named in the project brief. The backend ships the catalogue with every
 * analysis so this pane can show both what was detected and what was checked
 * for and not found — an empty result should read as "we looked", not as
 * "there are no biases here".
 */

import { el, section } from "../core/dom.js";
import { registerView } from "../core/registry.js";
import { severityTone } from "../core/format.js";
import { t } from "../core/i18n.js";
import { evidenceRefs, evidenceIdSet, badge, callout, notRunYet } from "./widgets.js";

/** Where a risk came from. Both sources agreeing is the strongest signal. */
const DETECTOR_TONE = { heuristic: "info", model: "brand", both: "critical" };

function detectorBadge(kind) {
  const key = DETECTOR_TONE[kind] ? kind : "model";
  return badge(t(`risks.detector.${key}`), DETECTOR_TONE[key],
    t(`risks.detector.${key}.title`));
}

function riskCard(risk, knownIds) {
  return el("article", { class: "card" }, [
    el("div", { class: "card__head" }, [
      el("span", { class: "card__title", text: risk.name }),
      badge(risk.severity || "medium", severityTone(risk.severity)),
      detectorBadge(risk.detected_by),
    ]),

    el("div", { class: "stack-2 small" }, [
      el("div", {}, [el("strong", { text: t("risks.where") }), risk.where]),
      risk.impact && el("div", {}, [el("strong", { text: t("risks.impact") }), risk.impact]),
      risk.mitigation && el("div", {}, [el("strong", { text: t("risks.mitigation") }), risk.mitigation]),
    ]),

    risk.evidence?.length
      ? el("div", { class: "row", style: { marginTop: "var(--sp-3)" } }, [
          el("span", { class: "xsmall faint", text: t("risks.triggeredBy") }),
          evidenceRefs(risk.evidence, knownIds),
        ])
      : null,
  ]);
}

/** Reference table: every bias in the brief, and whether it fired here. */
function catalogTable(catalog, risks) {
  const detected = new Set(risks.map((risk) => risk.bias));

  return el("div", { class: "card card--flush" }, [
    el("div", { class: "table-wrap" }, [
      el("table", { class: "table" }, [
        el("thead", {}, [
          el("tr", {}, [
            el("th", { text: t("risks.catalog.bias") }),
            el("th", { text: t("risks.catalog.appears") }),
            el("th", { text: t("risks.catalog.status") }),
          ]),
        ]),
        el("tbody", {}, catalog.map((entry) =>
          el("tr", {}, [
            el("td", {}, [el("strong", { text: entry.name })]),
            el("td", { class: "muted", text: entry.appears_as }),
            el("td", {}, [
              detected.has(entry.id)
                ? badge(t("risks.detected"), "critical")
                : badge(t("risks.notFound"), "ok"),
            ]),
          ]))),
      ]),
    ]),
  ]);
}

function renderRisks(state) {
  const { analysis } = state;
  if (!analysis) {
    return notRunYet(t("risks.empty"));
  }

  const risks = analysis.reasoning_risks || [];
  const catalog = analysis.bias_catalog || [];
  const knownIds = evidenceIdSet(analysis);

  const header = risks.length
    ? callout("warn", "⚠", t("risks.flagged.title", { count: risks.length }),
        t("risks.flagged.body"))
    : callout("ok", "✓", t("risks.clean.title"), t("risks.clean.body"));

  return el("div", { class: "stack" }, [
    header,

    risks.length
      ? section(t("risks.section"), t("risks.section.hint"),
          el("div", { class: "stack" }, risks.map((risk) => riskCard(risk, knownIds))))
      : null,

    catalog.length
      ? section(t("risks.catalog"), t("risks.catalog.hint"),
          catalogTable(catalog, risks))
      : null,

    callout("info", "i", t("risks.why.title"), t("risks.why.body")),
  ]);
}

registerView("risks", renderRisks);
