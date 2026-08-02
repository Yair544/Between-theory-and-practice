/**
 * evidenceView.js - the numbered evidence list.
 *
 * This pane is the ground truth of the whole tool. Everything else in the app
 * points back here, so it stays deliberately plain: the raw line, where it came
 * from, and nothing that could be mistaken for interpretation.
 */

import { el, section, qsa } from "../core/dom.js";
import { registerView } from "../core/registry.js";
import { formatTs, sourceLabel, formatCount } from "../core/format.js";
import { t } from "../core/i18n.js";
import { severityBadge, callout, notRunYet } from "./widgets.js";

/** Filter state lives here so typing does not trigger a full pane rebuild. */
let query = "";
let activeSource = "all";

function evidenceRow(item) {
  return el("div", {
    class: "evline",
    id: `ev-${item.id}`,
    dataset: {
      source: item.source,
      haystack: `${item.id} ${item.text} ${item.source}`.toLowerCase(),
    },
  }, [
    el("div", { class: "evline__id", text: item.id }),
    el("div", {}, [
      el("div", { class: "evline__text", text: item.text }),
      el("div", { class: "evline__meta" }, [
        el("span", { text: sourceLabel(item.source) }),
        item.line ? el("span", { text: t("evidence.line", { line: item.line }) }) : null,
        item.timestamp ? el("span", { text: formatTs(item.timestamp) }) : null,
        item.severity ? severityBadge(item.severity) : null,
      ]),
    ]),
  ]);
}

function applyFilter(root) {
  const q = query.trim().toLowerCase();
  let shown = 0;
  for (const row of qsa(".evline", root)) {
    const matchesSource = activeSource === "all" || row.dataset.source === activeSource;
    const matchesQuery = !q || row.dataset.haystack.includes(q);
    const visible = matchesSource && matchesQuery;
    row.classList.toggle("hidden", !visible);
    if (visible) shown += 1;
  }
  const counter = root.querySelector("[data-role='ev-count']");
  if (counter) counter.textContent = t("evidence.shown", { count: shown });
}

function toolbar(sources, root) {
  const search = el("input", {
    class: "input",
    type: "search",
    placeholder: t("evidence.filter"),
    value: query,
    onInput: (event) => { query = event.target.value; applyFilter(root); },
  });

  const chips = ["all", ...sources].map((source) =>
    el("button", {
      class: "chip",
      type: "button",
      "aria-pressed": String(source === activeSource),
      onClick: (event) => {
        activeSource = source;
        for (const chip of qsa(".chip", event.target.parentElement)) {
          chip.setAttribute("aria-pressed", String(chip === event.target));
        }
        applyFilter(root);
      },
    }, [source === "all" ? t("evidence.allSources") : sourceLabel(source)]));

  return el("div", { class: "stack-2", style: { marginBottom: "var(--sp-3)" } }, [
    el("div", { class: "row" }, [
      el("div", { class: "grow" }, [search]),
      el("span", { class: "xsmall faint", dataset: { role: "ev-count" } }),
    ]),
    el("div", { class: "row" }, chips),
  ]);
}

function renderEvidence(state) {
  const { analysis } = state;
  if (!analysis) {
    return notRunYet(t("evidence.empty"));
  }

  const items = analysis.evidence || [];
  if (!items.length) {
    return callout("warn", "!", t("evidence.none.title"), t("evidence.none.body"));
  }

  const sources = [...new Set(items.map((item) => item.source))];
  const list = el("div", { class: "card card--flush" }, items.map(evidenceRow));

  // The toolbar needs a reference to the container it filters, and the counter
  // it updates lives inside that same container - so build the root first.
  const root = el("div");
  root.append(toolbar(sources, root), list);

  // Filter once so the counter is populated on first paint.
  queueMicrotask(() => applyFilter(root));

  const stats = analysis.meta?.input_stats;

  return el("div", { class: "stack" }, [
    callout("info", "#", t("evidence.count.title", { count: formatCount(items.length) }),
      t("evidence.count.body")),
    stats?.redacted_count
      ? callout("ok", "🛡",
          t("evidence.redacted.title", { count: stats.redacted_count }),
          t("evidence.redacted.body"))
      : null,
    section(t("evidence.section"), t("evidence.section.hint"), root),
  ]);
}

registerView("evidence", renderEvidence);
