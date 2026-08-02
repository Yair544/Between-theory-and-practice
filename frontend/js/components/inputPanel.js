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
import { t } from "../core/i18n.js";

/** Field definitions: order here is the order shown in the sidebar. */
// `prose` fields follow the interface direction; the rest are machine text
// (logs, traces, alerts) and stay LTR even when the UI is Hebrew.
const FIELDS = [
  { key: "description", prose: true, help: true },
  { key: "logs", help: true },
  { key: "errors" },
  { key: "alerts" },
  { key: "deployNotes", prose: true, help: true },
  { key: "userReports", prose: true },
];

/** File extensions we are willing to read into a field. */
const ACCEPT = ".txt,.log,.json,.csv,.md,.out,.err";

function fieldBlock(field, value) {
  const label = t(`field.${field.key}.label`);
  const textarea = el("textarea", {
    class: field.prose ? "textarea textarea--prose" : "textarea",
    id: `input-${field.key}`,
    placeholder: t(`field.${field.key}.placeholder`),
    dir: field.prose ? null : "ltr",
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
      el("span", { text: label }),
      el("span", { class: "row" }, [
        counter,
        el("button", {
          class: "btn btn--ghost btn--sm",
          type: "button",
          title: t("input.file.title", { label }),
          onClick: () => fileInput.click(),
        }, [t("input.file")]),
      ]),
    ]),
    textarea,
    fileInput,
    field.help && el("div", { class: "field__help", text: t(`field.${field.key}.help`) }),
  ]);
}

function charLabel(value) {
  const n = (value || "").length;
  return n ? t("input.chars", { count: formatCount(n) }) : "";
}

/** Build the form and mount it into the sidebar. */
export function mountInputPanel() {
  const host = qs("#mount-input");
  if (!host) return;

  const state = getState();

  const titleField = el("div", { class: "field" }, [
    el("label", { class: "field__label", for: "input-title" }, [
      el("span", { text: t("input.title.label") }),
    ]),
    el("input", {
      class: "input",
      id: "input-title",
      placeholder: t("input.title.placeholder"),
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
