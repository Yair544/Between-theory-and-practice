/**
 * app.js - application entry point.
 *
 * Responsibilities, and nothing else:
 *   1. start the shell (theme, tabs, sidebar, status bar)
 *   2. mount each view into its pane
 *   3. re-render the active pane whenever the store changes
 *
 * Views are pure: given the state, return a node. They never reach outside
 * their own pane.
 */

import { initShell } from "./core/shell.js";
import { subscribe } from "./core/store.js";
import { render, emptyState, qs } from "./core/dom.js";

/**
 * Pane id -> render(state) => Node
 * Filled in as the individual views are implemented; anything missing falls
 * back to a placeholder so the shell is always navigable.
 */
const views = {};

/** Register a view for a pane. Called by each view module. */
export function registerView(paneId, renderFn) {
  views[paneId] = renderFn;
}

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

    const view = views[paneId];
    if (view) {
      render(container, view(state));
    } else {
      render(container, emptyState("○", "Nothing here yet", text));
    }
  }
}

function boot() {
  initShell();
  subscribe(renderPanes);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
