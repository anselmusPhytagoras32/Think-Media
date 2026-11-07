// FR01/W01, NFR03/05: nonpersonal, browser-local intro marker; never store session/PII.
const key = "thinkmedia.welcome.v1";
let seenInMemory = false;
export function hasSeenWelcome() {
  if (seenInMemory) return true;
  try {
    return localStorage.getItem(key) === "seen";
  } catch {
    return false;
  }
}
export function markWelcomeSeen() {
  seenInMemory = true;
  try {
    localStorage.setItem(key, "seen");
  } catch {
    /* Storage restrictions must never prevent entry. */
  }
}
