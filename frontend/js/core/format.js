/**
 * format.js - presentation helpers shared by every view.
 *
 * Confidence deserves a note. The backend gives us a number in [0, 1]; showing
 * "0.73" invites false precision, so we always show the number *and* a band,
 * and the bands deliberately stop short of "certain".
 */

/** 0.734 -> "73%" */
export function pct(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return `${Math.round(value * 100)}%`;
}

/**
 * Map a confidence score to a band label. The tool never says "confirmed":
 * confirming a root cause is a human decision made after running a test.
 */
export function confidenceBand(value) {
  if (value === null || value === undefined) return { label: "unrated", tone: "info" };
  if (value >= 0.7) return { label: "well supported", tone: "critical" };
  if (value >= 0.45) return { label: "plausible", tone: "high" };
  if (value >= 0.2) return { label: "weak", tone: "medium" };
  return { label: "speculative", tone: "low" };
}

/** Severity string -> badge modifier. Unknown values fall back to neutral. */
export function severityTone(severity) {
  const map = {
    critical: "critical", fatal: "critical", error: "critical",
    high: "high", warn: "high", warning: "high",
    medium: "medium", moderate: "medium",
    low: "low", info: "low", debug: "low",
  };
  return map[String(severity || "").toLowerCase()] || "info";
}

/** Priority string (P1..P4) -> badge modifier. */
export function priorityTone(priority) {
  const map = { p1: "critical", p2: "high", p3: "medium", p4: "low" };
  return map[String(priority || "").toLowerCase()] || "info";
}

/**
 * Render a timestamp for display. Incident timestamps arrive in whatever
 * format the source system used, so anything unparseable is shown verbatim
 * rather than silently replaced with "Invalid Date".
 */
export function formatTs(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  const pad = (n) => String(n).padStart(2, "0");
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ` +
    `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  );
}

/** 1234 -> "1.2 s"; 340 -> "340 ms" */
export function formatDuration(ms) {
  if (ms === null || ms === undefined) return "";
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
}

/** 12043 -> "12,043" */
export function formatCount(n) {
  return Number(n || 0).toLocaleString("en-US");
}

/** Human label for a source key coming from the backend. */
export function sourceLabel(source) {
  const map = {
    description: "Incident description",
    logs: "Application logs",
    errors: "Error traces",
    alerts: "Monitoring alerts",
    deploy_notes: "Deployment notes",
    user_reports: "User reports",
  };
  return map[source] || source;
}

/** Truncate for a one-line preview without cutting mid-word where avoidable. */
export function truncate(text, max = 120) {
  const value = String(text || "");
  if (value.length <= max) return value;
  const cut = value.slice(0, max);
  const lastSpace = cut.lastIndexOf(" ");
  return `${(lastSpace > max * 0.6 ? cut.slice(0, lastSpace) : cut).trimEnd()}…`;
}
