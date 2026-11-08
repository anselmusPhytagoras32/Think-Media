// FR08: real suggestions embedded in discovery; failures leave primary flows available.
import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { api } from "./api";
import { suggestionReason } from "./copy";
type Suggested = { item: { id: string; title: string }; reason: string };
export function SuggestionsPreview({
  kind,
  onOpen,
  browseHint,
}: {
  kind: "listing" | "content";
  onOpen: (id: string) => void;
  browseHint?: string;
}) {
  const [items, setItems] = useState<Suggested[]>([]),
    [busy, setBusy] = useState(true),
    [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    let active = true;
    api<{ listings: Suggested[]; content: Suggested[] }>(
      "/recommendations?limit=3",
    )
      .then((data) => {
        if (active) setItems(kind === "listing" ? data.listings : data.content);
      })
      .catch(() => {
        if (active) setUnavailable(true);
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [kind]);
  return (
    <section className="panel suggestions-preview">
      <h2>Suggestions to explore</h2>
      <p className="muted">
        Suggestions support your preparation and do not determine application
        decisions.
      </p>
      {busy ? (
        <p className="muted" role="status">
          Loading suggestions…
        </p>
      ) : unavailable ? (
        <p className="muted">
          Suggestions are unavailable.{" "}
          {browseHint || "You can continue browsing below."}
        </p>
      ) : items.length ? (
        items.map(({ item, reason }) => (
          <div className="preview-row" key={item.id}>
            <div>
              <button className="text-button" onClick={() => onOpen(item.id)}>
                {item.title}
              </button>
              <p>{suggestionReason(reason)}</p>
            </div>
            <button
              className="preview-open"
              aria-label={`Open ${item.title}`}
              onClick={() => onOpen(item.id)}
            >
              <ArrowRight size={18} />
            </button>
          </div>
        ))
      ) : (
        <p className="muted">
          No eligible suggestions yet.{" "}
          {browseHint || "Browse available items below or update your profile."}
        </p>
      )}
    </section>
  );
}
