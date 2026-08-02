/**
 * app.js - application entry point.
 *
 * Responsibilities, and nothing else:
 *   1. start the shell (theme, tabs, sidebar, status bar)
 *   2. mount the sidebar components
 *   3. re-render the workspace panes whenever the store changes
 *
 * Views are pure: given the state, return a node. They never reach outside
 * their own pane, and they register themselves via core/registry.js.
 */

import { initShell } from "./core/shell.js";
import { getState, subscribe } from "./core/store.js";
import { render, emptyState, qs } from "./core/dom.js";
import { getView } from "./core/registry.js";
import { mountInputPanel, syncInputPanel } from "./components/inputPanel.js";
import { mountSamplePicker, renderSamples } from "./components/samplePicker.js";
import { mountRunPanel } from "./components/runPanel.js";

// Each view module registers itself with registerView() on import.
import "./views/summaryView.js";
import "./views/evidenceView.js";
import "./views/timelineView.js";
import "./views/hypothesesView.js";
import "./views/risksView.js";
import "./views/actionsView.js";
import "./views/reportView.js";

/** Shown for any pane that has no view registered yet. */
const PLACEHOLDER_TEXT = {
  summary: "Load a sample incident or paste your own evidence, then press Analyse.",
  evidence: "Every line of input becomes a numbered evidence item that AI claims must cite.",
  timeline: "A reconstructed sequence of events, marked as observed or inferred.",
  hypotheses: "Several competing explanations, each with evidence for and against it.",
  risks: "Cognitive biases and logical fallacies detected in this investigation.",
  actions: "Concrete debugging steps, each tied to the evidence that motivates it.",
  report: "A draft postmortem you can hand to a technical or non-technical audience.",
};

function renderPanes(state) {
  for (const [paneId, text] of Object.entries(PLACEHOLDER_TEXT)) {
    const container = qs(`#pane-${paneId}`);
    if (!container) continue;

    const view = getView(paneId);
    render(container, view
      ? view(state)
      : emptyState("○", "Not implemented yet", text));
  }
}

function boot() {
  initShell();

  // Sidebar: built once, then kept in sync imperatively. Rebuilding textareas
  // on every keystroke would destroy the caret position.
  mountInputPanel();
  mountRunPanel();
  mountSamplePicker();

  // ...but a language switch does have to rebuild it, because the labels and
  // placeholders live in the markup. The typed text is preserved by reading it
  // back out of the store, which is the only reason the sidebar can be
  // rebuilt safely at all.
  let lastLanguage = getState().language;
  subscribe((state) => {
    if (state.language === lastLanguage) return;
    lastLanguage = state.language;
    mountInputPanel();
    syncInputPanel();
    renderSamples();
  });

  // Workspace: fully re-rendered from state on every change.
  subscribe(renderPanes);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
