/**
 * shell.js - behaviour that belongs to the application frame rather than to
 * any single view: theme, sidebar, tab strip, status bar.
 */

import { qs, qsa } from "./dom.js";
import { getState, setState, subscribe } from "./store.js";
import { formatDuration, pct } from "./format.js";

const THEME_KEY = "iq.theme";

/* ------------------------------------------------------------------ theme */

export function initTheme() {
  const button = qs("#btn-theme");
  if (!button) return;

  // The glyph shows the theme you would switch TO, not the current one.
  const sync = () => {
    const dark = document.documentElement.dataset.theme === "dark";
    button.textContent = dark ? "☀" : "☽";
    button.title = dark ? "Switch to light theme" : "Switch to dark theme";
  };
  sync();

  button.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem(THEME_KEY, next); } catch { /* private mode */ }
    sync();
  });
}

/* ---------------------------------------------------------------- sidebar */

export function initSidebar() {
  const body = qs("#app-body");
  const button = qs("#btn-toggle-sidebar");
  if (!body || !button) return;
  button.addEventListener("click", () => {
    const collapsed = body.dataset.sidebar === "collapsed";
    body.dataset.sidebar = collapsed ? "expanded" : "collapsed";
    button.setAttribute("aria-pressed", String(!collapsed));
  });
}

/* ------------------------------------------------------------------- tabs */

export function initTabs() {
  const strip = qs("#tabstrip");
  if (!strip) return;

  strip.addEventListener("click", (event) => {
    const tab = event.target.closest(".tab");
    if (tab && !tab.disabled) setState({ activeTab: tab.dataset.tab });
  });

  // Left/right arrows move between tabs, as expected for role="tablist".
  strip.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    const tabs = qsa(".tab", strip).filter((t) => !t.disabled);
    const current = tabs.findIndex((t) => t.dataset.tab === getState().activeTab);
    const step = event.key === "ArrowRight" ? 1 : -1;
    const next = tabs[(current + step + tabs.length) % tabs.length];
    if (next) { setState({ activeTab: next.dataset.tab }); next.focus(); }
    event.preventDefault();
  });

  subscribe((state) => {
    for (const tab of qsa(".tab", strip)) {
      const selected = tab.dataset.tab === state.activeTab;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
    }
    for (const pane of qsa(".pane")) {
      pane.classList.toggle("is-active", pane.dataset.pane === state.activeTab);
    }
    syncTabCounts(state);
  });
}

/**
 * Per-tab result counters, so the tab strip doubles as a table of contents:
 * "Hypotheses 4 · Reasoning risks 2" reads before any pane is opened.
 * The risks counter goes red when something was flagged - that one number is
 * the tool's whole thesis in the chrome.
 */
function syncTabCounts(state) {
  const analysis = state.analysis;
  const counts = analysis
    ? {
        evidence: analysis.evidence?.length,
        timeline: analysis.timeline?.length,
        hypotheses: analysis.hypotheses?.length,
        risks: analysis.reasoning_risks?.length,
        actions: analysis.next_actions?.length,
      }
    : {};

  for (const node of qsa(".tab__count")) {
    const value = counts[node.dataset.count];
    node.textContent = value ? String(value) : "";
    if (node.dataset.count === "risks" && value) {
      node.dataset.tone = "alert";
    } else {
      delete node.dataset.tone;
    }
  }
}

/* -------------------------------------------------------------- statusbar */

export function initStatusBar() {
  const stateEl = qs("#status-state");
  const dotEl = qs("#status-dot");
  const groundingEl = qs("#status-grounding");
  const modelEl = qs("#status-model");
  const durationEl = qs("#status-duration");
  const providerBadge = qs("#provider-badge");

  subscribe((state) => {
    const { status, progress, error, analysis } = state;

    if (stateEl) {
      const labels = {
        idle: "Ready — load a sample or paste evidence",
        running: progress || "Analysing…",
        done: "Analysis complete",
        error: `Failed: ${error || "unknown error"}`,
      };
      stateEl.textContent = labels[status] || "";
    }

    if (dotEl) {
      dotEl.dataset.tone =
        status === "running" ? "running" : status === "error" ? "error" : "idle";
    }

    const meta = analysis?.meta;

    if (providerBadge) {
      if (!meta) {
        providerBadge.textContent = "not run yet";
        providerBadge.className = "badge";
      } else if (meta.offline) {
        providerBadge.textContent = "offline engine";
        providerBadge.className = "badge badge--medium";
        providerBadge.title =
          "No language model was used. Only the deterministic engine produced this analysis.";
      } else {
        providerBadge.textContent = `${meta.provider} · ${meta.model}`;
        providerBadge.className = "badge badge--brand";
        providerBadge.title = "Model-assisted analysis, verified against the input evidence";
      }
    }

    if (groundingEl) {
      const score = analysis?.verification?.grounding_score;
      groundingEl.textContent =
        score === undefined || score === null ? "" : `grounding ${pct(score)}`;
      groundingEl.title = "Share of model claims that cite evidence actually present in the input";
    }

    if (modelEl) modelEl.textContent = meta?.model ? `model ${meta.model}` : "";
    if (durationEl) {
      durationEl.textContent = meta?.duration_ms ? formatDuration(meta.duration_ms) : "";
    }
  });
}

/** Wire up everything that is not a view. */
export function initShell() {
  initTheme();
  initSidebar();
  initTabs();
  initStatusBar();
}
