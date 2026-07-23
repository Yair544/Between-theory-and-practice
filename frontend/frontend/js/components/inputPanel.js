/**
 * inputPanel.js - the evidence entry form in the sidebar.
 *
 * The brief lists six kinds of incident input. They are kept as separate
 * fields rather than one big textarea because the backend tags every evidence
 * item with its source, and "the deploy notes said X" is a materially
 * different claim from "a user said X".
 */

import { el, render, qs } from "../core/dom.js";
import { getState, setState } from "../core/store.js";
import { formatCount } from "../core/format.js";

/** Field definitions: order here is the order shown in the sidebar. */
const FIELDS = [
  {
    key: "description",
    label: "Incident description",
    prose: true,
    placeholder: "What is failing, since when, and who noticed?",
    help: "One or two sentences. This is context, not evidence.",
  },
  {
    key: "logs",
    label: "Application logs",
    placeholder: "2026-05-02T10:14:03Z ERROR checkout ...",
    help: "Paste raw lines. Timestamps are used to build the timeline.",
  },
  {
    key: "errors",
    label: "Error traces",
    placeholder: "Traceback (most recent call last): ...",
  },
  {
    key: "alerts",
    label: "Monitoring alerts",
    placeholder: "[FIRING] CheckoutErrorRate > 5% for 10m",
  },
  {
    key: "deployNotes",
    label: "Recent deployment notes",
    prose: true,
    placeholder: "v2.4.1 - switched payment client to connection pooling",
    help: "A deploy before an incident is a lead, not a cause.",
  },
  {
    key: "userReports",
    label: "User complaints / support tickets",
    prose: true,
    placeholder: "\"Card declined at checkout\" x14 since 10:20",
  },
];

/** File extensions we are willing to read into a field. */
const ACCEPT = ".txt,.log,.json,.csv,.md,.out,.err";

function fieldBlock(field, value) {
  const textarea = el("textarea", {
    class: field.prose ? "textarea textarea--prose" : "textarea",
    id: `input-${field.key}`,
    placeholder: field.placeholder || "",
    spellcheck: "false",
    onInput: (event) => {
      setState({ input: { [field.key]: event.target.value } });
      counter.textContent = charLabel(event.target.value);
    },
  }, [value || ""]);

  const counter = el("span", { class: "field__counter", text: charLabel(value) });

  const fileInput = el("input", {
    type: "file",
    class: "hidden",
    accept: ACCEPT,
    onChange: async (event) => {
      const file = event.target.files?.[0];
      if (!file) return;
      const text = await file.text();
      const merged = textarea.value ? `${textarea.value}\n${text}` : text;
      textarea.value = merged;
      counter.textContent = charLabel(merged);
      setState({ input: { [field.key]: merged } });
      event.target.value = "";
    },
  });

  return el("div", { class: "field" }, [
    el("label", { class: "field__label", for: `input-${field.key}` }, [
      el("span", { text: field.label }),
      el("span", { class: "row" }, [
        counter,
        el("button", {
          class: "btn btn--ghost btn--sm",
          type: "button",
          title: `Load a file into "${field.label}"`,
          onClick: () => fileInput.click(),
        }, ["file"]),
      ]),
    ]),
    textarea,
    fileInput,
    field.help && el("div", { class: "field__help", text: field.help }),
  ]);
}

function charLabel(value) {
  const n = (value || "").length;
  return n ? `${formatCount(n)} chars` : "";
}

/** Build the form and mount it into the sidebar. */
export function mountInputPanel() {
  const host = qs("#mount-input");
  if (!host) return;

  const state = getState();

  const titleField = el("div", { class: "field" }, [
    el("label", { class: "field__label", for: "input-title" }, [
      el("span", { text: "Incident title" }),
    ]),
    el("input", {
      class: "input",
      id: "input-title",
      placeholder: "Checkout failures after v2.4.1",
      value: state.input.title || "",
      onInput: (e) => setState({ input: { title: e.target.value } }),
    }),
  ]);

  render(host, [
    titleField,
    ...FIELDS.map((field) => fieldBlock(field, state.input[field.key])),
  ]);
}

/**
 * Push store values back into the DOM. Used after loading a sample, which
 * changes the input without the user typing.
 */
export function syncInputPanel() {
  const state = getState();
  const title = qs("#input-title");
  if (title) title.value = state.input.title || "";

  for (const field of FIELDS) {
    const node = qs(`#input-${field.key}`);
    if (!node) continue;
    node.value = state.input[field.key] || "";
    const counter = node.parentElement?.querySelector(".field__counter");
    if (counter) counter.textContent = charLabel(node.value);
  }
}
