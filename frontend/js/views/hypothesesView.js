/**
 * hypothesesView.js - competing explanations, ranked but never decided.
 *
 * Design rules enforced here:
 *   - always show more than one explanation, even when one looks obvious
 *   - evidence FOR and evidence AGAINST get equal visual weight
 *   - a hypothesis with no contradicting evidence is called out as suspicious,
 *     because "nothing contradicts it" usually means nobody looked
 *   - the recommended test is what turns a hypothesis into a fact; it is the
 *     last thing on the card, where an action belongs
 */

import { el, section } from "../core/dom.js";
import { registerView } from "../core/registry.js";
import { confidenceBand } from "../core/format.js";
import { t } from "../core/i18n.js";
import {
  evidenceRefs, evidenceIdSet, confidenceMeter, badge, callout, notRunYet,
} from "./widgets.js";

function evidenceColumn(kind, ids, knownIds) {
  const isFor = kind === "for";
  return el("div", { class: `evidence-col evidence-col--${kind}` }, [
    el("div", { class: "evidence-col__title", text: t(isFor ? "hyp.for" : "hyp.against") }),
    ids?.length
      ? evidenceRefs(ids, knownIds)
      : el("div", {
          class: "xsmall faint",
          text: t(isFor ? "hyp.noneFound" : "hyp.noneLooked"),
        }),
  ]);
}

function hypothesisCard(hypothesis, index, knownIds) {
  const band = confidenceBand(hypothesis.confidence);
  const against = hypothesis.contradicting_evidence || [];
  const support = hypothesis.supporting_evidence || [];

  return el("article", { class: "card" }, [
    el("div", { class: "card__head" }, [
      badge(`H${index + 1}`, "hypothesis"),
      el("span", { class: "card__title", text: hypothesis.title }),
      badge(band.label, band.tone),
      confidenceMeter(hypothesis.confidence),
    ]),

    el("div", { class: "card__body prose", text: hypothesis.explanation }),

    el("div", { class: "evidence-split" }, [
      evidenceColumn("for", support, knownIds),
      evidenceColumn("against", against, knownIds),
    ]),

    // A one-sided hypothesis is the classic shape of confirmation bias.
    support.length && !against.length
      ? el("div", { style: { marginTop: "var(--sp-3)" } }, [
          callout("warn", "⚖", t("hyp.oneSided.title"), t("hyp.oneSided.body")),
        ])
      : null,

    hypothesis.recommended_test
      ? el("div", { style: { marginTop: "var(--sp-4)" } }, [
          el("div", { class: "evidence-col", style: { borderInlineStart: "3px solid var(--c-brand)" } }, [
            el("div", { class: "evidence-col__title", style: { color: "var(--c-brand)" },
                        text: t("hyp.test") }),
            el("div", { class: "small", text: hypothesis.recommended_test }),
          ]),
        ])
      : null,

    hypothesis.rebuttal
      ? el("div", { style: { marginTop: "var(--sp-3)" } }, [
          callout("info", "↺", t("hyp.rebuttal"), hypothesis.rebuttal),
        ])
      : null,
  ]);
}

function renderHypotheses(state) {
  const { analysis } = state;
  if (!analysis) {
    return notRunYet(t("hyp.empty"));
  }

  const hypotheses = [...(analysis.hypotheses || [])]
    .sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));
  const knownIds = evidenceIdSet(analysis);

  if (!hypotheses.length) {
    return callout("warn", "!", t("hyp.none.title"), t("hyp.none.body"));
  }

  const top = hypotheses[0];
  const gap = hypotheses.length > 1
    ? (top.confidence ?? 0) - (hypotheses[1].confidence ?? 0)
    : 1;

  return el("div", { class: "stack" }, [
    callout("info", "≡", t("hyp.count.title", { count: hypotheses.length }),
      t("hyp.count.body")),

    // A near-tie is useful information: it means the evidence does not
    // discriminate between the top two, so picking either one is a coin flip.
    gap < 0.1 && hypotheses.length > 1
      ? callout("warn", "≈", t("hyp.tie.title"), t("hyp.tie.body"))
      : null,

    section(t("hyp.section"), t("hyp.section.hint"),
      el("div", { class: "stack" },
        hypotheses.map((hypothesis, index) => hypothesisCard(hypothesis, index, knownIds)))),
  ]);
}

registerView("hypotheses", renderHypotheses);
