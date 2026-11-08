// FR01–11 / NFR05: stable local routes for reload, browser Back and deep links.
import { useEffect, useState } from "react";
export const pages = [
  "overview",
  "profile",
  "opportunities",
  "applications",
  "review",
  "suggestions",
  "learning",
  "assistant",
  "verification",
  "content",
  "reports",
  "audit",
  "more",
] as const;
export type PageKey = (typeof pages)[number];
export function href(page: string, id?: string) {
  return `#/${page}${id ? "/" + encodeURIComponent(id) : ""}`;
}
function safeDecode(value: string) {
  try {
    return decodeURIComponent(value);
  } catch {
    return undefined;
  }
}
function readRoute() {
  const [path, query = ""] = window.location.hash
    .replace(/^#\/?/, "")
    .split("?");
  const [page, id] = path.split("/");
  const params = new URLSearchParams(query);
  const filters = new URLSearchParams();
  if (params.get("search") || params.get("q"))
    filters.set("q", params.get("search") || params.get("q") || "");
  if (["ojt", "job"].includes(params.get("type") || ""))
    filters.set("type", params.get("type") || "");
  for (const key of ["location", "skill"])
    if (params.get(key)) filters.set(key, params.get(key) || "");
  return {
    page: pages.includes(page as PageKey)
      ? (page as PageKey)
      : ("overview" as PageKey),
    id: id ? safeDecode(id) : undefined,
    create: new URLSearchParams(query).get("new") === "1",
    query,
    filters: filters.toString(),
  };
}
export function useRoute() {
  const [route, setRoute] = useState(readRoute);
  useEffect(() => {
    const change = () => setRoute(readRoute());
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  return {
    route,
    navigate: (page: string, id?: string) => {
      window.location.hash = href(page, id);
    },
  };
}
