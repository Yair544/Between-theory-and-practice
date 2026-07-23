/**
 * toast.js - transient notifications.
 * Errors stay until dismissed; everything else auto-hides.
 */

import { el, qs } from "./dom.js";

const ICONS = { info: "ℹ", ok: "✓", warn: "⚠", error: "✕" };

/**
 * @param {string} message
 * @param {Object} [options]
 * @param {"info"|"ok"|"warn"|"error"} [options.type="info"]
 * @param {number} [options.timeout] ms; 0 keeps it until clicked.
 */
export function toast(message, { type = "info", timeout } = {}) {
  const host = qs("#toast-host");
  if (!host) return;

  const life = timeout ?? (type === "error" ? 0 : 4000);

  const node = el("div", {
    class: `toast toast--${type}`,
    role: "status",
    title: "Click to dismiss",
    onClick: () => node.remove(),
  }, [
    el("span", { class: "callout__icon", text: ICONS[type] || ICONS.info }),
    el("span", { class: "grow", text: message }),
  ]);

  host.appendChild(node);
  if (life > 0) setTimeout(() => node.remove(), life);
  return node;
}
