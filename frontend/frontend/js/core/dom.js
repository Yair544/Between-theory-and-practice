/**
 * dom.js - the only place in the frontend that touches document.createElement.
 *
 * Every view builds its markup by composing el() calls instead of assembling
 * HTML strings. That is deliberate: incident logs are attacker-influenced text,
 * and building nodes with textContent means a log line containing "<script>"
 * can never become executable markup.
 */

/**
 * Create an element.
 *
 * @param {string} tag
 * @param {Object} [props]  class, text, html (trusted only), dataset, attrs,
 *                          plus on* handlers, e.g. onClick.
 * @param {Array}  [children] Nodes, strings, or null/false (skipped).
 * @returns {HTMLElement}
 */
export function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);

  for (const [key, value] of Object.entries(props)) {
    if (value === null || value === undefined || value === false) continue;

    if (key === "class") {
      node.className = value;
    } else if (key === "text") {
      node.textContent = String(value);
    } else if (key === "dataset") {
      Object.assign(node.dataset, value);
    } else if (key === "style") {
      Object.assign(node.style, value);
    } else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else {
      node.setAttribute(key, value === true ? "" : String(value));
    }
  }

  append(node, children);
  return node;
}

/** Append a child, a list of children, or plain text. Nullish entries skipped. */
export function append(parent, children) {
  const list = Array.isArray(children) ? children : [children];
  for (const child of list) {
    if (child === null || child === undefined || child === false) continue;
    parent.appendChild(
      child instanceof Node ? child : document.createTextNode(String(child))
    );
  }
  return parent;
}

/** Document fragment from a list of children. */
export function frag(children) {
  return append(document.createDocumentFragment(), children);
}

/** Remove every child of a node. */
export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
  return node;
}

/** Replace a container's contents in one go. */
export function render(container, children) {
  return append(clear(container), children);
}

export const qs = (selector, root = document) => root.querySelector(selector);
export const qsa = (selector, root = document) =>
  Array.from(root.querySelectorAll(selector));

/** Shorthand for the standard empty-state block. */
export function emptyState(icon, title, text) {
  return el("div", { class: "empty" }, [
    el("div", { class: "empty__icon", text: icon }),
    el("div", { class: "empty__title", text: title }),
    text && el("div", { class: "empty__text", text }),
  ]);
}

/** A titled section wrapper used by every analysis view. */
export function section(title, hint, body) {
  return el("section", {}, [
    el("div", { class: "section__head" }, [
      el("h2", { class: "section__title", text: title }),
      hint && el("span", { class: "section__hint", text: hint }),
    ]),
    body,
  ]);
}
