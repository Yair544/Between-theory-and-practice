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
    toast("Postmortem copied to the clipboard", { type: "ok" });
  } catch {
    toast("The browser blocked clipboard access — use Download instead.", { type: "warn" });
  }
}

function renderReport(state) {
  const { analysis } = state;
  if (!analysis) {
    return notRunYet("A draft postmortem is generated from the analysis and can be exported as Markdown.");
  }

  const markdown = analysis.report_markdown;
  if (!markdown) {
    return callout("warn", "!", "No postmortem generated",
      "The analysis completed but produced no report body.");
  }

  const slug = (analysis.title || "incident")
    .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 48);

  return el("div", { class: "stack" }, [
    callout("warn", "✎", "This is a draft, not a published postmortem",
      "It is assembled from hypotheses that have not been tested yet. Confirm the " +
      "root cause with a real test, delete the hypotheses that fail, and put your " +
      "own name on it before circulating."),

    section("Draft postmortem", "Markdown, ready to paste into a wiki or a PR",
      el("div", { class: "stack" }, [
        el("div", { class: "row" }, [
          el("button", { class: "btn btn--primary", onClick: () => copy(markdown) }, ["Copy Markdown"]),
          el("button", {
            class: "btn",
            onClick: () => {
              download(`postmortem-${slug || "incident"}.md`, markdown);
              toast("Saved to your downloads folder", { type: "ok" });
            },
          }, ["Download .md"]),
          el("span", { class: "grow" }),
          el("span", { class: "xsmall faint", text: `${markdown.length.toLocaleString("en-US")} characters` }),
        ]),
        el("pre", { class: "code-block" }, [markdown]),
      ])),
  ]);
}

registerView("report", renderReport);
