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
        item.line ? el("span", { text: `line ${item.line}` }) : null,
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
  if (counter) counter.textContent = `${shown} shown`;
}

function toolbar(sources, root) {
  const search = el("input", {
    class: "input",
    type: "search",
    placeholder: "Filter evidence…",
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
    }, [source === "all" ? "all sources" : sourceLabel(source)]));

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
    return notRunYet("Once an analysis runs, every input line appears here with a stable ID.");
  }

  const items = analysis.evidence || [];
  if (!items.length) {
    return callout("warn", "!", "No evidence extracted",
      "Nothing in the input could be turned into an evidence item. " +
      "Check that the logs are plain text rather than a screenshot or binary file.");
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
    callout("info", "#", `${formatCount(items.length)} evidence items`,
      "Every claim the tool makes cites these IDs. A claim with no ID next to it " +
      "is a claim nobody has checked."),
    stats?.redacted_count
      ? callout("ok", "🛡",
          `${stats.redacted_count} value(s) redacted before leaving this machine`,
          "Emails, IP addresses, bearer tokens and card-shaped numbers were replaced " +
          "with placeholders. The originals never reached the model provider.")
      : null,
    section("Evidence", "grouped by source, filterable", root),
  ]);
}

registerView("evidence", renderEvidence);
