// NFR03/05/09: nonpersonal navigation preference; blocked storage stays usable.
export type SidebarPreference = "auto" | "expanded" | "collapsed" | null;
// A prior width choice did not express consent to lock the new automatic rail.
const key = "thinkmedia.sidebar.v2";
export function readSidebarPreference(): SidebarPreference {
  try {
    const value = localStorage.getItem(key);
    return value === "auto" || value === "expanded" || value === "collapsed"
      ? value
      : null;
  } catch {
    return null;
  }
}
export function saveSidebarPreference(value: Exclude<SidebarPreference, null>) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* Preference remains in React state. */
  }
}
