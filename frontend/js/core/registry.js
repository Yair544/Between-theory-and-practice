/**
 * registry.js - maps a pane id to the function that renders it.
 *
 * This lives outside app.js on purpose. Views need registerView, and app.js
 * needs the views; putting the registry in its own module breaks the import
 * cycle that would otherwise leave `views` in the temporal dead zone when the
 * first view module evaluates.
 */

const views = new Map();

/**
 * @param {string} paneId matches the data-pane attribute in index.html
 * @param {(state: object) => Node} renderFn pure: state in, node out
 */
export function registerView(paneId, renderFn) {
  views.set(paneId, renderFn);
}

export function getView(paneId) {
  return views.get(paneId);
}

export function paneIds() {
  return [...views.keys()];
}
