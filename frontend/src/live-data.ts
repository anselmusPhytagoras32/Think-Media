// FR01–11/NFR03/11: invalidation signals contain topics only, never account or application data.
import { useEffect, useState } from "react";

export type DataTopic = "accounts" | "marketplace" | "learning" | "recommendations";
const listeners = new Set<(topics: DataTopic[]) => void>();
const allTopics: DataTopic[] = ["accounts", "marketplace", "learning", "recommendations"];
let channel: BroadcastChannel | null = null;
function emit(topics: DataTopic[]) {
  if (document.visibilityState === "hidden") return;
  for (const listener of listeners) listener(topics);
}
function validTopics(value: unknown): DataTopic[] {
  return Array.isArray(value) ? value.filter((topic): topic is DataTopic => allTopics.includes(topic)) : [];
}
export function notifyMutation(path: string) {
  let topics: DataTopic[] = [];
  if (/^\/(auth|profiles|admin\/companies)(\/|$)/.test(path)) topics = ["accounts", "marketplace", "recommendations"];
  else if (/^\/(company\/listings|listings|applications)(\/|$)/.test(path)) topics = ["marketplace", "recommendations"];
  else if (/^\/(content|admin\/content|reports|admin\/reports)(\/|$)/.test(path)) topics = ["learning", "recommendations"];
  else if (path === "/interactions") topics = ["recommendations"];
  if (!topics.length) return;
  // Let the initiating form finish its own successful transition first.
  window.setTimeout(() => { emit(topics); channel?.postMessage(topics); }, 200);
}
function connect() {
  const refresh = () => emit(allTopics);
  window.addEventListener("focus", refresh);
  document.addEventListener("visibilitychange", refresh);
  const timer = window.setInterval(refresh, 5000);
  if ("BroadcastChannel" in window) {
    channel = new BroadcastChannel("thinkmedia-data-changed");
    channel.onmessage = (event) => emit(validTopics(event.data));
  }
  return () => {
    window.removeEventListener("focus", refresh);
    document.removeEventListener("visibilitychange", refresh);
    window.clearInterval(timer);
    channel?.close(); channel = null;
  };
}
let disconnect: (() => void) | null = null;
export function useDataRevision(topics: DataTopic[], enabled = true) {
  const [revision, setRevision] = useState(0);
  const key = topics.join(",");
  useEffect(() => {
    if (!enabled) return;
    const wanted = key.split(",");
    const listener = (changed: DataTopic[]) => { if (changed.some((topic) => wanted.includes(topic))) setRevision((old) => old + 1); };
    listeners.add(listener);
    if (listeners.size === 1) disconnect = connect();
    return () => {
      listeners.delete(listener);
      if (!listeners.size) { disconnect?.(); disconnect = null; }
    };
  }, [key, enabled]);
  return revision;
}
