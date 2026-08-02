/**
 * reportView.js - the draft postmortem.
 *
 * "Draft" is not modesty. The document is generated from the analysis, and the
 * analysis is a set of hypotheses, so publishing it unedited would present
 * guesses as conclusions. The banner says so, and so does the document header.
 */

import { el, section } from "../core/dom.js";
import { registerView } from "../core/registry.js";
import { toast } from "../core/toast.js";
import { t } from "../core/i18n.js";
import { callout, notRunYet } from "./widgets.js";

function download(filename, text) {
  const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = el("a", { href: url, download: filename });
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast(t("report.copied"), { type: "ok" });
  } catch {
    toast(t("report.copyFailed"), { type: "warn" });
  }
}

function renderReport(state) {
  const { analysis } = state;
  if (!analysis) {
    return notRunYet(t("report.empty"));
  }

  const markdown = analysis.report_markdown;
  if (!markdown) {
    return callout("warn", "!", t("report.none.title"), t("report.none.body"));
  }

  const slug = (analysis.title || "incident")
    .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 48);

  return el("div", { class: "stack" }, [
    callout("warn", "✎", t("report.draft.title"), t("report.draft.body")),

    section(t("report.section"), t("report.section.hint"),
      el("div", { class: "stack" }, [
        el("div", { class: "row" }, [
          el("button", { class: "btn btn--primary", onClick: () => copy(markdown) }, [t("report.copy")]),
          el("button", {
            class: "btn",
            onClick: () => {
              download(`postmortem-${slug || "incident"}.md`, markdown);
              toast(t("report.downloaded"), { type: "ok" });
            },
          }, [t("report.download")]),
          el("span", { class: "grow" }),
          el("span", { class: "xsmall faint",
            text: t("report.chars", { count: markdown.length.toLocaleString("en-US") }) }),
        ]),
        el("pre", { class: "code-block", dir: "ltr" }, [markdown]),
      ])),
  ]);
}

registerView("report", renderReport);
