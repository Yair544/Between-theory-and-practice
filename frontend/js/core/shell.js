/**
 * shell.js - behaviour that belongs to the application frame rather than to
 * any single view: theme, sidebar, tab strip, status bar.
 */

import { el, qs, qsa, render } from "./dom.js";
import { getState, setState, subscribe } from "./store.js";
import { formatDuration, pct } from "./format.js";
import { LANGUAGES, applyLanguage, detectLanguage, getLanguage, t } from "./i18n.js";

const THEME_KEY = "iq.theme";

/* ------------------------------------------------------------------ theme */

/**
 * Re-label the theme button. Module-level because the language switch has to
 * call it too - the glyph is language-independent, the tooltip is not.
 */
function syncThemeButton() {
  const button = qs("#btn-theme");
  if (!button) return;
  // The glyph shows the theme you would switch TO, not the current one.
  const dark = document.documentElement.dataset.theme === "dark";
  button.textContent = dark ? "☀" : "☽";
  button.title = t(dark ? "app.theme.toLight" : "app.theme.toDark");
  button.setAttribute("aria-label", button.title);
}

export function initTheme() {
  const button = qs("#btn-theme");
  if (!button) return;
  syncThemeButton();

  button.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem(THEME_KEY, next); } catch { /* private mode */ }
    syncThemeButton();
  });
}

/* --------------------------------------------------------------- language */

/**
 * Build the EN / עב toggle.
 *
 * Rendered from the LANGUAGES list rather than hard-coded in markup, so adding
 * a third language is a dictionary entry and nothing else. Deliberately not a
 * flag: a flag names a country, not a language, and on Windows the flag emoji
 * degrades to two letter-boxes anyway.
 */
export function initLanguage() {
  const host = qs("#langswitch");
  if (!host) return;

  const paint = () => {
    const active = getLanguage();
    render(host, LANGUAGES.map((lang) =>
      el("button", {
        class: "langswitch__btn",
        type: "button",
        lang: lang.code,
        "aria-pressed": String(lang.code === active),
        title: lang.name,
        onClick: () => {
          if (lang.code === getLanguage()) return;
          applyLanguage(lang.code);
          // Views are pure functions of state, so this one line redraws them.
          setState({ language: lang.code });
          paint();
          syncThemeButton();
        },
      }, [lang.label])));
  };

  applyLanguage(detectLanguage());
  setState({ language: getLanguage() });
  paint();
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
        idle: t("status.idle"),
        running: progress || t("status.running"),
        done: t("status.done"),
        error: t("status.error", { error: error || "unknown" }),
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
        providerBadge.textContent = t("provider.notRun");
        providerBadge.className = "badge";
        providerBadge.title = "";
      } else if (meta.offline) {
        providerBadge.textContent = t("provider.offline");
        providerBadge.className = "badge badge--medium";
        providerBadge.title = t("provider.offline.title");
      } else {
        providerBadge.textContent = `${meta.provider} · ${meta.model}`;
        providerBadge.className = "badge badge--brand";
        providerBadge.title = t("provider.online.title");
      }
    }

    if (groundingEl) {
      const score = analysis?.verification?.grounding_score;
      groundingEl.textContent =
        score === undefined || score === null ? "" : t("status.grounding", { value: pct(score) });
      groundingEl.title = t("status.grounding.title");
    }

    if (modelEl) modelEl.textContent = meta?.model ? t("status.model", { model: meta.model }) : "";
    if (durationEl) {
      durationEl.textContent = meta?.duration_ms ? formatDuration(meta.duration_ms) : "";
    }
  });
}

/** Wire up everything that is not a view. */
export function initShell() {
  // Language first: everything below reads translated strings.
  initLanguage();
  initTheme();
  initSidebar();
  initTabs();
  initStatusBar();
}
