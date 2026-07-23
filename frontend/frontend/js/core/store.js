/**
 * store.js - a minimal observable state container.
 *
 * The whole UI is a pure function of this object: components never read from
 * the DOM to decide what to draw, and nothing outside store.js mutates state.
 */

const initialState = {
  /** "idle" | "running" | "done" | "error" */
  status: "idle",
  /** Human-readable progress line shown in the status bar while running. */
  progress: "",
  /** The last error message, if any. */
  error: null,

  /** Raw user input, mirrored from the input panel. */
  input: {
    title: "",
    description: "",
    logs: "",
    errors: "",
    alerts: "",
    deployNotes: "",
    userReports: "",
  },

  /** Sample incidents advertised by the backend. */
  samples: [],
  activeSampleId: null,

  /** The analysis document returned by POST /api/analyze. */
  analysis: null,

  /** Which workspace tab is visible. */
  activeTab: "summary",
};

let state = structuredClone(initialState);
const listeners = new Set();

/** Current state. Treat the result as read-only. */
export function getState() {
  return state;
}

/**
 * Shallow-merge a patch into state and notify subscribers.
 * `input` is merged one level deeper so callers can patch a single field.
 */
export function setState(patch) {
  const next = { ...state, ...patch };
  if (patch.input) next.input = { ...state.input, ...patch.input };
  state = next;
  for (const listener of listeners) listener(state);
  return state;
}

/** Subscribe to every state change. Returns an unsubscribe function. */
export function subscribe(listener) {
  listeners.add(listener);
  listener(state);
  return () => listeners.delete(listener);
}

/** Back to the initial state, keeping the sample list we already fetched. */
export function resetAnalysis() {
  setState({
    status: "idle",
    progress: "",
    error: null,
    analysis: null,
    activeTab: "summary",
  });
}

/** True when there is enough input to be worth sending to the backend. */
export function hasUsableInput(s = state) {
  const { description, logs, errors, alerts, deployNotes, userReports } = s.input;
  return [description, logs, errors, alerts, deployNotes, userReports]
    .some((field) => field && field.trim().length >= 10);
}
