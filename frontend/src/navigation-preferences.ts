// NFR03/05/09: nonpersonal navigation preference; blocked storage stays usable.
export type SidebarPreference = "expanded" | "collapsed" | null;
const key = "thinkmedia.sidebar.v1";
export function readSidebarPreference(): SidebarPreference {
  try {
    const value = localStorage.getItem(key);
    return value === "expanded" || value === "collapsed" ? value : null;
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
