/**
 * summaryView.js - the landing pane.
 *
 * Layout order is a deliberate argument: the reader sees how trustworthy the
 * analysis is (verification banner) *before* they read what it says.
 */

import { el, section } from "../core/dom.js";
import { registerView } from "../core/registry.js";
import { pct } from "../core/format.js";
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
    return callout("warn", "⚙", "Offline mode",
      "No language model was consulted. Everything below was produced by the " +
      "deterministic engine: pattern-matched evidence, a timestamp-ordered timeline, " +
      "and rule-based hypotheses. Add an API key in .env for the model-assisted analysis.");
  }

  if (!unsupported.length && !invalid.length) {
    return callout("ok", "✓", `Every claim traced to evidence (grounding ${pct(score)})`,
      "Each statement below cites at least one input item that exists. " +
      "Traceable is not the same as correct — the cited evidence may itself be misleading.");
  }

  return callout("danger", "!",
    `${unsupported.length + invalid.length} claim(s) failed verification (grounding ${pct(score)})`,
    el("div", { class: "stack-2" }, [
      invalid.length ? el("div", {}, [
        el("strong", { text: "Invented citations: " }),
        `the model cited ${invalid.map((c) => c.citation).join(", ")}, which do not exist in the input.`,
      ]) : null,
      unsupported.length ? el("div", {}, [
        el("strong", { text: "Unsupported statements: " }),
        `${unsupported.length} claim(s) cite no evidence at all.`,
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

  return section("What happened", "professional summary, no unsupported claims",
    el("div", { class: "card" }, [
      el("div", { class: "prose", text: summary.text || "No summary produced." }),
      el("div", { class: "row", style: { marginTop: "var(--sp-3)" } }, [
        el("span", { class: "xsmall faint", text: "based on" }),
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
      badge("facts", "fact"),
      el("span", { class: "card__title", text: "Directly supported by the input" }),
      el("span", { class: "xsmall faint", text: `${facts.length}` }),
    ]),
    facts.length
      ? el("ul", { class: "stack-2", style: { paddingLeft: "var(--sp-5)" } },
          facts.map((fact) => el("li", {}, [
            el("span", { text: fact.statement }),
            el("span", { style: { marginLeft: "var(--sp-2)" } }, [evidenceRefs(fact.evidence, ids)]),
          ])))
      : el("div", { class: "muted small", text: "No statement in the analysis was fully grounded." }),
  ]);

  const assumptionCard = el("div", { class: "card" }, [
    el("div", { class: "card__head" }, [
      badge("assumptions", "assumption"),
      el("span", { class: "card__title", text: "Believed but not proven" }),
      el("span", { class: "xsmall faint", text: `${assumptions.length}` }),
    ]),
    assumptions.length
      ? el("div", { class: "stack" },
          assumptions.map((item) => el("div", {}, [
            el("div", { text: item.statement }),
            item.why && el("div", { class: "xsmall faint", text: `Why we think so: ${item.why}` }),
            item.how_to_verify && el("div", { class: "xsmall" }, [
              el("strong", { text: "To confirm: " }),
              item.how_to_verify,
            ]),
          ])))
      : el("div", { class: "muted small", text: "No assumptions were flagged." }),
  ]);

  return section("Facts vs assumptions",
    "the two are kept apart on purpose — mixing them is how investigations go wrong",
    el("div", { class: "stack" }, [factCard, assumptionCard]));
}

/* ------------------------------------------------------ role-based rewrites */

function audienceView(analysis) {
  const audiences = analysis.summary?.audiences;
  if (!audiences) return null;

  const labels = {
    engineer: "For the on-call engineer",
    manager: "For the engineering manager",
    support: "For the support team",
  };

  return section("Same facts, three audiences",
    "the wording changes, the claims do not",
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

  return section("Still unknown", "questions that must be answered before closing this incident",
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
    return callout("danger", "✕", "Analysis failed", error || "Unknown error.");
  }
  if (!analysis) {
    return notRunYet(
      "Load one of the example incidents from the sidebar, or paste your own logs, " +
      "then press Analyse incident."
    );
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
