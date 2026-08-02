/**
 * summaryView.js - the landing pane.
 *
 * Layout order is a deliberate argument: the reader sees how trustworthy the
 * analysis is (verification banner) *before* they read what it says.
 */

import { el, section } from "../core/dom.js";
import { registerView } from "../core/registry.js";
import { pct } from "../core/format.js";
import { t } from "../core/i18n.js";
import {
  evidenceRefs, evidenceIdSet, badge, callout, notRunYet,
} from "./widgets.js";

/* ------------------------------------------------------------- verification */

function verificationBanner(analysis) {
  const v = analysis.verification || {};
  const unsupported = v.unsupported || [];
  const invalid = v.invalid_citations || [];
  const score = v.grounding_score;

  if (analysis.meta?.offline) {
    return callout("warn", "⚙", t("summary.offline.title"), t("summary.offline.body"));
  }

  if (!unsupported.length && !invalid.length) {
    return callout("ok", "✓",
      t("summary.verified.title", { value: pct(score) }), t("summary.verified.body"));
  }

  return callout("danger", "!",
    t("summary.failedChecks.title",
      { count: unsupported.length + invalid.length, value: pct(score) }),
    el("div", { class: "stack-2" }, [
      invalid.length ? el("div", {}, [
        el("strong", { text: t("summary.invented") }),
        t("summary.invented.body", { list: invalid.map((c) => c.citation).join(", ") }),
      ]) : null,
      unsupported.length ? el("div", {}, [
        el("strong", { text: t("summary.unsupported") }),
        t("summary.unsupported.body", { count: unsupported.length }),
      ]) : null,
      el("ul", { style: { marginTop: "var(--sp-2)", marginBottom: 0 } },
        unsupported.slice(0, 5).map((item) =>
          el("li", {}, [
            el("span", { class: "small", text: item.statement }),
            el("span", { class: "xsmall faint", text: ` — ${item.where}` }),
          ]))),
    ]));
}

/* ------------------------------------------------------------- what happened */

function headline(analysis) {
  const ids = evidenceIdSet(analysis);
  const summary = analysis.summary || {};

  return section(t("summary.what"), t("summary.what.hint"),
    el("div", { class: "card" }, [
      el("div", { class: "prose", text: summary.text || t("summary.noSummary") }),
      el("div", { class: "row", style: { marginTop: "var(--sp-3)" } }, [
        el("span", { class: "xsmall faint", text: t("summary.basedOn") }),
        evidenceRefs(summary.citations, ids),
      ]),
    ]));
}

/* ------------------------------ facts / assumptions (required by the brief) */

function factsAndAssumptions(analysis) {
  const ids = evidenceIdSet(analysis);
  const facts = analysis.facts || [];
  const assumptions = analysis.assumptions || [];

  const factCard = el("div", { class: "card" }, [
    el("div", { class: "card__head" }, [
      badge(t("summary.facts"), "fact"),
      el("span", { class: "card__title", text: t("summary.facts.title") }),
      el("span", { class: "xsmall faint", text: `${facts.length}` }),
    ]),
    facts.length
      ? el("ul", { class: "stack-2", style: { paddingLeft: "var(--sp-5)" } },
          facts.map((fact) => el("li", {}, [
            el("span", { text: fact.statement }),
            el("span", { style: { marginLeft: "var(--sp-2)" } }, [evidenceRefs(fact.evidence, ids)]),
          ])))
      : el("div", { class: "muted small", text: t("summary.facts.none") }),
  ]);

  const assumptionCard = el("div", { class: "card" }, [
    el("div", { class: "card__head" }, [
      badge(t("summary.assumptions"), "assumption"),
      el("span", { class: "card__title", text: t("summary.assumptions.title") }),
      el("span", { class: "xsmall faint", text: `${assumptions.length}` }),
    ]),
    assumptions.length
      ? el("div", { class: "stack" },
          assumptions.map((item) => el("div", {}, [
            el("div", { text: item.statement }),
            item.why && el("div", { class: "xsmall faint",
              text: t("summary.assumption.why", { why: item.why }) }),
            item.how_to_verify && el("div", { class: "xsmall" }, [
              el("strong", { text: t("summary.assumption.verify") }),
              item.how_to_verify,
            ]),
          ])))
      : el("div", { class: "muted small", text: t("summary.assumptions.none") }),
  ]);

  return section(t("summary.factsVsAssumptions"), t("summary.factsVsAssumptions.hint"),
    el("div", { class: "stack" }, [factCard, assumptionCard]));
}

/* ------------------------------------------------------ role-based rewrites */

function audienceView(analysis) {
  const audiences = analysis.summary?.audiences;
  if (!audiences) return null;

  const labels = {
    engineer: t("summary.audience.engineer"),
    manager: t("summary.audience.manager"),
    support: t("summary.audience.support"),
  };

  return section(t("summary.audiences"), t("summary.audiences.hint"),
    el("div", { class: "stack" },
      Object.entries(labels)
        .filter(([key]) => audiences[key])
        .map(([key, label]) => el("div", { class: "card card--tight" }, [
          el("div", { class: "card__head" }, [badge(key, "brand"), el("span", { class: "card__title", text: label })]),
          el("div", { class: "small", text: audiences[key] }),
        ]))));
}

/* --------------------------------------------------------- open questions */

function openQuestions(analysis) {
  const questions = analysis.open_questions || [];
  if (!questions.length) return null;

  return section(t("summary.openQuestions"), t("summary.openQuestions.hint"),
    el("div", { class: "card" }, [
      el("ul", { class: "stack-2", style: { paddingLeft: "var(--sp-5)", marginBottom: 0 } },
        questions.map((q) => el("li", {}, [
          el("div", { text: q.question }),
          q.why_it_matters && el("div", { class: "xsmall faint", text: q.why_it_matters }),
        ]))),
    ]));
}

/* -------------------------------------------------------------------- view */

function renderSummary(state) {
  const { analysis, status, error } = state;

  if (status === "error") {
    return callout("danger", "✕", t("summary.failed"), error || "");
  }
  if (!analysis) {
    return notRunYet(t("summary.empty"));
  }

  return el("div", { class: "stack" }, [
    verificationBanner(analysis),
    headline(analysis),
    factsAndAssumptions(analysis),
    audienceView(analysis),
    openQuestions(analysis),
  ]);
}

registerView("summary", renderSummary);
