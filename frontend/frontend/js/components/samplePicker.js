/**
 * samplePicker.js - loads one of the bundled example incidents.
 *
 * These exist so the tool can be evaluated in one click, and so we can compare
 * runs against a fixed input when testing prompt changes.
 */

import { el, render, qs, emptyState } from "../core/dom.js";
import { setState, getState } from "../core/store.js";
import { api } from "../core/api.js";
import { toast } from "../core/toast.js";
import { syncInputPanel } from "./inputPanel.js";

function sampleButton(sample) {
  const active = getState().activeSampleId === sample.id;
  return el("button", {
    class: `btn btn--block ${active ? "btn--primary" : ""}`,
    style: { justifyContent: "flex-start", textAlign: "left" },
    title: sample.description || sample.title,
    onClick: () => loadSample(sample.id),
  }, [
    el("span", { class: "grow" }, [
      el("div", { style: { fontWeight: "600" }, text: sample.title }),
      el("div", { class: "xsmall faint", text: sample.scenario || "" }),
    ]),
  ]);
}

async function loadSample(id) {
  try {
    const sample = await api.getSample(id);
    setState({
      activeSampleId: id,
      analysis: null,
      status: "idle",
      error: null,
      input: {
        title: sample.title || "",
        description: sample.description || "",
        logs: sample.logs || "",
        errors: sample.errors || "",
        alerts: sample.alerts || "",
        deployNotes: sample.deploy_notes || "",
        userReports: sample.user_reports || "",
      },
    });
    syncInputPanel();
    renderSamples();
    toast(`Loaded "${sample.title}"`, { type: "ok" });
  } catch (error) {
    toast(error.message, { type: "error" });
  }
}

export function renderSamples() {
  const host = qs("#mount-samples");
  if (!host) return;

  const samples = getState().samples;
  if (!samples.length) {
    render(host, el("div", { class: "xsmall faint" }, [
      "No example incidents found in data/samples/.",
    ]));
    return;
  }
  render(host, samples.map(sampleButton));
}

/** Fetch the sample list once at start-up. */
export async function mountSamplePicker() {
  const host = qs("#mount-samples");
  if (!host) return;

  render(host, el("div", { class: "row xsmall faint" }, [
    el("span", { class: "spinner" }),
    "loading examples…",
  ]));

  try {
    const samples = await api.listSamples();
    setState({ samples });
  } catch {
    setState({ samples: [] });
  }
  renderSamples();
}
