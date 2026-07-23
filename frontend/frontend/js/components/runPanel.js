/**
 * runPanel.js - the Analyse button, its options, and progress feedback.
 */

import { el, render, qs } from "../core/dom.js";
import { getState, setState, resetAnalysis, hasUsableInput, subscribe } from "../core/store.js";
import { api, ApiError } from "../core/api.js";
import { toast } from "../core/toast.js";
import { syncInputPanel } from "./inputPanel.js";

/** Steps shown while the request is in flight. Purely informational. */
const STEPS = [
  "Extracting evidence items",
  "Reconstructing the timeline",
  "Generating competing hypotheses",
  "Checking claims against the evidence",
  "Scanning for reasoning risks",
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
    toast("Add some evidence first — a description or a few log lines.", { type: "warn" });
    return;
  }

  const controller = new AbortController();
  inFlight = controller;
  setState({ status: "running", progress: STEPS[0], error: null, analysis: null });

  // Advance the progress label on a timer. This is cosmetic: the backend
  // returns one response, so we cannot know the real stage. Labelled as an
  // estimate in the UI rather than pretending to be a live trace.
  let step = 0;
  const ticker = setInterval(() => {
    step = Math.min(step + 1, STEPS.length - 1);
    setState({ progress: STEPS[step] });
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
      options,
    }, controller.signal);

    setState({ status: "done", progress: "", analysis, activeTab: "summary" });

    const unsupported = analysis.verification?.unsupported?.length || 0;
    if (unsupported) {
      toast(
        `${unsupported} model claim${unsupported === 1 ? "" : "s"} could not be traced to the input. ` +
        "See the Summary tab.",
        { type: "warn", timeout: 8000 }
      );
    }
    if (analysis.meta?.offline) {
      toast("Ran in offline mode — no language model was consulted.", { type: "warn" });
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
        STEPS.map((label) => {
          const current = STEPS.indexOf(state.progress);
          const index = STEPS.indexOf(label);
          const stepState = index < current ? "done" : index === current ? "active" : "pending";
          return el("div", { class: "progress-step", dataset: { state: stepState } }, [
            stepState === "active" ? el("span", { class: "spinner" }) : el("span", { text: stepState === "done" ? "✓" : "○" }),
            label,
          ]);
        }))
    : null;

  render(host, [
    el("div", { class: "stack-2", style: { marginBottom: "var(--sp-4)" } }, [
      optionRow("devils_advocate", "Argue against the leading hypothesis",
        "Runs a second pass that tries to falsify the top answer."),
      optionRow("redact_pii", "Redact emails, IPs and tokens before sending",
        "Nothing that looks like a secret leaves this machine."),
    ]),

    el("button", {
      class: "btn btn--primary btn--block btn--lg",
      disabled: running ? "disabled" : null,
      onClick: runAnalysis,
    }, running ? [el("span", { class: "spinner" }), "Analysing…"] : ["Analyse incident"]),

    el("div", { class: "row", style: { marginTop: "var(--sp-2)" } }, [
      running
        ? el("button", { class: "btn btn--sm grow", onClick: cancelAnalysis }, ["Cancel"])
        : el("button", { class: "btn btn--sm grow", onClick: clearAll }, ["Clear everything"]),
    ]),

    progressBlock && el("div", { style: { marginTop: "var(--sp-4)" } }, [progressBlock]),

    el("div", { class: "field__help", style: { marginTop: "var(--sp-3)" } }, [
      "IncidentIQ proposes hypotheses. It does not decide the root cause — " +
      "run the suggested test before you believe any of them.",
    ]),
  ]);
}

export function mountRunPanel() {
  // Re-render only when the run status or progress label actually changes.
  // Rebuilding on every keystroke would fight the input panel for focus.
  let last = null;
  subscribe((state) => {
    const key = `${state.status}|${state.progress}`;
    if (key === last) return;
    last = key;
    renderRunPanel();
  });
}
