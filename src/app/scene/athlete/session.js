import { DEFAULT_COMPOSITION, normalizeComposition } from './catalog.js';

// A fresh page always starts with the original mannequin. Client navigation
// keeps the user's subsequent choice until the next full reload/new startup.
let activeComposition = { ...DEFAULT_COMPOSITION };
export function getSessionComposition() {
  return { ...activeComposition };
}
export function setSessionComposition(value) {
  activeComposition = normalizeComposition(value);
  return getSessionComposition();
}
