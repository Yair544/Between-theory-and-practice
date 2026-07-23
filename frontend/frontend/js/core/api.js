/**
 * api.js - the single boundary between the UI and the FastAPI backend.
 *
 * No component calls fetch() directly, so switching transport or adding auth
 * later is a one-file change.
 */

const BASE = "/api";

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, { method = "GET", body, signal } = {}) {
  let response;
  try {
    response = await fetch(BASE + path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (cause) {
    if (cause.name === "AbortError") throw cause;
    throw new ApiError(
      "Could not reach the IncidentIQ server. Is it still running?",
      0,
      String(cause)
    );
  }

  const isJson = (response.headers.get("content-type") || "").includes("application/json");
  const payload = isJson ? await response.json().catch(() => null) : await response.text();

  if (!response.ok) {
    const detail = payload && payload.detail ? payload.detail : payload;
    throw new ApiError(
      typeof detail === "string" ? detail : `Request failed (${response.status})`,
      response.status,
      detail
    );
  }
  return payload;
}

export const api = {
  /** Provider, model, and whether a key is configured. */
  health: () => request("/health"),

  /** Metadata for the bundled example incidents. */
  listSamples: () => request("/samples"),

  /** Full evidence payload for one example incident. */
  getSample: (id) => request(`/samples/${encodeURIComponent(id)}`),

  /**
   * Run the analysis pipeline.
   * @param {Object} payload the `input` slice of the store
   * @param {AbortSignal} [signal]
   */
  analyze: (payload, signal) => request("/analyze", { method: "POST", body: payload, signal }),

  /** Markdown postmortem for an analysis the server still has cached. */
  exportMarkdown: (analysisId) =>
    request(`/analysis/${encodeURIComponent(analysisId)}/report.md`),
};
