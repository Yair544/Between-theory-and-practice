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
import { evidenceRefs, evidenceIdSet, badge, callout, notRunYet } from "./widgets.js";

/** Where a risk came from. Both sources agreeing is the strongest signal. */
const DETECTOR_LABEL = {
  heuristic: { text: "rule-based", tone: "info",
    title: "Flagged by a deterministic rule in the backend, independent of any model." },
  model: { text: "model", tone: "brand",
    title: "Flagged by the language model reviewing its own reasoning." },
  both: { text: "rule + model", tone: "critical",
    title: "Flagged independently by both the deterministic rule and the model." },
};

function riskCard(risk, knownIds) {
  const detector = DETECTOR_LABEL[risk.detected_by] || DETECTOR_LABEL.model;

  return el("article", { class: "card" }, [
    el("div", { class: "card__head" }, [
      el("span", { class: "card__title", text: risk.name }),
      badge(risk.severity || "medium", severityTone(risk.severity)),
      badge(detector.text, detector.tone, detector.title),
    ]),

    el("div", { class: "stack-2 small" }, [
      el("div", {}, [el("strong", { text: "Where it showed up: " }), risk.where]),
      risk.impact && el("div", {}, [el("strong", { text: "Effect on the investigation: " }), risk.impact]),
      risk.mitigation && el("div", {}, [el("strong", { text: "How to reduce it: " }), risk.mitigation]),
    ]),

    risk.evidence?.length
      ? el("div", { class: "row", style: { marginTop: "var(--sp-3)" } }, [
          el("span", { class: "xsmall faint", text: "triggered by" }),
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
            el("th", { text: "Bias or fallacy" }),
            el("th", { text: "How it can appear in this project" }),
            el("th", { text: "Status" }),
          ]),
        ]),
        el("tbody", {}, catalog.map((entry) =>
          el("tr", {}, [
            el("td", {}, [el("strong", { text: entry.name })]),
            el("td", { class: "muted", text: entry.appears_as }),
            el("td", {}, [
              detected.has(entry.id)
                ? badge("detected", "critical")
                : badge("checked, not found", "ok"),
            ]),
          ]))),
      ]),
    ]),
  ]);
}

function renderRisks(state) {
  const { analysis } = state;
  if (!analysis) {
    return notRunYet("Cognitive biases and logical fallacies found in this investigation appear here.");
  }

  const risks = analysis.reasoning_risks || [];
  const catalog = analysis.bias_catalog || [];
  const knownIds = evidenceIdSet(analysis);

  const header = risks.length
    ? callout("warn", "⚠", `${risks.length} reasoning risk(s) flagged`,
        "These describe how the investigation may be going wrong, not what broke in " +
        "production. Read them before acting on the hypotheses.")
    : callout("ok", "✓", "No reasoning risks flagged",
        "The checks below all ran and found nothing. That is weaker evidence than it " +
        "sounds: the detectors only see the reasoning that was written down.");

  return el("div", { class: "stack" }, [
    header,

    risks.length
      ? section("Flagged risks", "sorted by severity",
          el("div", { class: "stack" }, risks.map((risk) => riskCard(risk, knownIds))))
      : null,

    catalog.length
      ? section("What was checked",
          "the eight biases and fallacies named in the project brief",
          catalogTable(catalog, risks))
      : null,

    callout("info", "i", "Why this pane exists",
      "AI output reads as confident and professional whether or not it is correct. " +
      "Automation bias is the risk that a fluent answer gets accepted because it is " +
      "fluent. The tool cannot remove that risk — it can only keep pointing at it."),
  ]);
}

registerView("risks", renderRisks);
