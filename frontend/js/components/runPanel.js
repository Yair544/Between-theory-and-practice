/**
 * runPanel.js - the Analyse button, its options, and progress feedback.
 */

import { el, render, qs } from "../core/dom.js";
import { getState, setState, resetAnalysis, hasUsableInput, subscribe } from "../core/store.js";
import { api, ApiError } from "../core/api.js";
import { toast } from "../core/toast.js";
import { t } from "../core/i18n.js";
import { syncInputPanel } from "./inputPanel.js";

/**
 * Steps shown while the request is in flight. Stored as keys, not strings, so
 * the progress list follows the interface language - and so the index-based
 * progress tracking keeps working when the labels change length.
 */
const STEP_KEYS = [
  "progress.evidence",
  "progress.timeline",
  "progress.hypotheses",
  "progress.verify",
  "progress.risks",
];

let inFlight = null;

const options = {
  devils_advocate: true,
  redact_pii: true,
  hypothesis_count: 4,
};

function optionRow(key, label, help) {
  return el("label", { class: "checkbox" }, [
    el("input", {
      type: "checkbox",
      checked: options[key] ? "checked" : null,
      onChange: (event) => { options[key] = event.target.checked; },
    }),
    el("span", {}, [
      el("div", { text: label }),
      help && el("div", { class: "xsmall faint", text: help }),
    ]),
  ]);
}

async function runAnalysis() {
  if (inFlight) return;

  const state = getState();
  if (!hasUsableInput(state)) {
    toast(t("run.needInput"), { type: "warn" });
    return;
  }

  const controller = new AbortController();
  inFlight = controller;
  setState({ status: "running", progress: STEP_KEYS[0], error: null, analysis: null });

  // Advance the progress label on a timer. This is cosmetic: the backend
  // returns one response, so we cannot know the real stage. Labelled as an
  // estimate in the UI rather than pretending to be a live trace.
  let step = 0;
  const ticker = setInterval(() => {
    step = Math.min(step + 1, STEP_KEYS.length - 1);
    setState({ progress: STEP_KEYS[step] });
  }, 2500);

  try {
    const analysis = await api.analyze({
      title: state.input.title,
      description: state.input.description,
      logs: state.input.logs,
      errors: state.input.errors,
      alerts: state.input.alerts,
      deploy_notes: state.input.deployNotes,
      user_reports: state.input.userReports,
      // The model writes its prose in whatever the interface is set to.
      options: { ...options, language: state.language },
    }, controller.signal);

    setState({ status: "done", progress: "", analysis, activeTab: "summary" });

    const unsupported = analysis.verification?.unsupported?.length || 0;
    if (unsupported) {
      toast(t("run.unsupportedToast", { count: unsupported }), { type: "warn", timeout: 8000 });
    }
    if (analysis.meta?.offline) {
      toast(t("run.offlineToast"), { type: "warn" });
    }
  } catch (error) {
    if (error.name === "AbortError") {
      setState({ status: "idle", progress: "" });
    } else {
      const message = error instanceof ApiError ? error.message : String(error);
      setState({ status: "error", progress: "", error: message });
      toast(message, { type: "error" });
    }
  } finally {
    clearInterval(ticker);
    inFlight = null;
    renderRunPanel();
  }
}

function cancelAnalysis() {
  inFlight?.abort();
}

function clearAll() {
  setState({
    activeSampleId: null,
    input: {
      title: "", description: "", logs: "", errors: "",
      alerts: "", deployNotes: "", userReports: "",
    },
  });
  resetAnalysis();
  syncInputPanel();
}

export function renderRunPanel() {
  const host = qs("#mount-run");
  if (!host) return;

  const state = getState();
  const running = state.status === "running";

  const progressBlock = running
    ? el("div", { class: "progress-steps" },
        STEP_KEYS.map((key, index) => {
          const current = STEP_KEYS.indexOf(state.progress);
          const stepState = index < current ? "done" : index === current ? "active" : "pending";
          return el("div", { class: "progress-step", dataset: { state: stepState } }, [
            stepState === "active"
              ? el("span", { class: "spinner" })
              : el("span", { text: stepState === "done" ? "✓" : "○" }),
            t(key),
          ]);
        }))
    : null;

  render(host, [
    el("div", { class: "stack-2", style: { marginBottom: "var(--sp-4)" } }, [
      optionRow("devils_advocate", t("run.devilsAdvocate"), t("run.devilsAdvocate.help")),
      optionRow("redact_pii", t("run.redact"), t("run.redact.help")),
    ]),

    el("button", {
      class: "btn btn--primary btn--block btn--lg",
      disabled: running ? "disabled" : null,
      title: "Ctrl+Enter",
      onClick: runAnalysis,
    }, running ? [el("span", { class: "spinner" }), t("run.analysing")] : [t("run.analyse")]),

    running ? null : el("div", {
      class: "xsmall faint",
      style: { textAlign: "center", marginTop: "var(--sp-2)" },
    }, [el("kbd", { text: "Ctrl" }), " + ", el("kbd", { text: "Enter" }), ` ${t("run.shortcut")}`]),

    el("div", { class: "row", style: { marginTop: "var(--sp-2)" } }, [
      running
        ? el("button", { class: "btn btn--sm grow", onClick: cancelAnalysis }, [t("run.cancel")])
        : el("button", { class: "btn btn--sm grow", onClick: clearAll }, [t("run.clear")]),
    ]),

    progressBlock && el("div", { style: { marginTop: "var(--sp-4)" } }, [progressBlock]),

    el("div", { class: "field__help", style: { marginTop: "var(--sp-3)" } }, [
      t("run.disclaimer"),
    ]),
  ]);
}

export function mountRunPanel() {
  // Re-render only when the run status or progress label actually changes.
  // Rebuilding on every keystroke would fight the input panel for focus.
  let last = null;
  subscribe((state) => {
    const key = `${state.status}|${state.progress}|${state.language}`;
    if (key === last) return;
    last = key;
    renderRunPanel();
  });

  // Ctrl+Enter runs the analysis from anywhere - including from inside a
  // textarea, which is where the user's hands already are after pasting logs.
  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      runAnalysis();
    }
  });
}
