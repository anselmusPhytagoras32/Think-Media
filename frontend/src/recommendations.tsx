// FR08–09: real eligible suggestions and optional explicit relevance ratings.
import { FormEvent, useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  BriefcaseBusiness,
  Check,
  RefreshCw,
  UserRound,
} from "lucide-react";
import { Account, api } from "./api";
import { suggestionReason } from "./copy";
import { Marketplace } from "./marketplace";
import { Learning } from "./learning";
type Item = {
  id: string;
  title: string;
  company_name?: string;
  location?: string;
  summary?: string;
  description?: string;
  skills?: string[];
  tags?: string[];
};
type Suggestion = { item: Item; reason: string; score: number };
type Suggestions = {
  listings: Suggestion[];
  content: Suggestion[];
  mode: "profile" | "hybrid" | "general";
  alpha: number;
  limitations: string[];
};
function Rating({ item, kind }: { item: Item; kind: "listing" | "content" }) {
  const [rating, setRating] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [success, setSuccess] = useState("");
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      await api("/interactions", "POST", {
        item_type: kind,
        item_id: item.id,
        event_type: "rating",
        rating: Number(rating),
      });
      setSuccess("Your relevance rating was saved.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="rating-form" onSubmit={submit}>
      <div className="field">
        <label htmlFor={`rating-${kind}-${item.id}`}>
          Relevance rating (optional)
        </label>
        <select
          id={`rating-${kind}-${item.id}`}
          required
          value={rating}
          onChange={(e) => setRating(e.target.value)}
        >
          <option value="">Choose a rating</option>
          <option value="1">1 · Not relevant</option>
          <option value="2">2 · Slightly relevant</option>
          <option value="3">3 · Somewhat relevant</option>
          <option value="4">4 · Relevant</option>
          <option value="5">5 · Very relevant</option>
        </select>
      </div>
      <button className="secondary" disabled={busy || !rating}>
        {busy ? "Saving…" : "Share rating"}
      </button>
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
      {success && (
        <p className="rating-saved" role="status">
          <Check size={15} />
          {success}
        </p>
      )}
    </form>
  );
}
export function Recommendations({
  account,
  onProfile,
  onOpen,
}: {
  account: Account;
  onProfile: () => void;
  onOpen?: (kind: "listing" | "content", id: string) => void;
}) {
  const [data, setData] = useState<Suggestions | null>(null),
    [busy, setBusy] = useState(true),
    [error, setError] = useState(""),
    [target, setTarget] = useState<{
      kind: "listing" | "content";
      id: string;
    } | null>(null);
  async function load() {
    setBusy(true);
    setError("");
    try {
      setData(await api<Suggestions>("/recommendations?limit=10"));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    void load();
  }, []);
  function open(kind: "listing" | "content", id: string) {
    void api("/interactions", "POST", {
      item_type: kind,
      item_id: id,
      event_type: "view",
    }).catch(() => {});
    if (onOpen) onOpen(kind, id);
    else setTarget({ kind, id });
  }
  if (target)
    return (
      <>
        <button className="back-button" onClick={() => setTarget(null)}>
          <ArrowLeft size={16} />
          Back to suggestions
        </button>
        {target.kind === "listing" ? (
          <Marketplace account={account} mode="browse" initialId={target.id} />
        ) : (
          <Learning initialId={target.id} />
        )}
      </>
    );
  const rows = (items: Suggestion[], kind: "listing" | "content") =>
    items.length ? (
      items.map(({ item, reason }) => (
        <article className="suggestion-row" key={item.id}>
          <div className="suggestion-content">
            <h3>
              <button onClick={() => open(kind, item.id)}>{item.title}</button>
            </h3>
            {item.company_name && (
              <p className="company-name">
                {item.company_name}
                {item.location ? " · " + item.location : ""}
              </p>
            )}
            <p>{(item.summary || item.description || "").slice(0, 220)}</p>
            <div className="suggestion-reason">
              <Check size={15} />
              {suggestionReason(reason)}
            </div>
            <button className="text-button" onClick={() => open(kind, item.id)}>
              {kind === "listing" ? "View opportunity" : "Read resource"}
              <ArrowRight size={15} />
            </button>
          </div>
          <Rating item={item} kind={kind} />
        </article>
      ))
    ) : (
      <div className="empty">
        <p>
          No eligible {kind === "listing" ? "opportunities" : "resources"} to
          suggest yet. Check again when new items are published.
        </p>
      </div>
    );
  return (
    <>
      <header className="page-heading">
        <div>
          <h1>Suggestions for you</h1>
          <p>
            Explore open opportunities and learning resources based on your
            profile.
          </p>
        </div>
        <button
          className="secondary"
          disabled={busy}
          onClick={() => void load()}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </header>
      <div className="suggestions-intro">
        <p>
          These are suggestions, not placement or hiring decisions. Optional
          relevance ratings help improve suggestions and do not affect your
          applications.
        </p>
        <button className="text-button" onClick={onProfile}>
          <UserRound size={17} />
          Update your skills and interests
        </button>
      </div>
      {error && (
        <div className="notice error" role="alert">
          {error}
        </div>
      )}
      {busy ? (
        <p role="status">Finding eligible suggestions…</p>
      ) : (
        data && (
          <>
            <p className="suggestion-mode">
              {data.mode === "general"
                ? "Getting started: explore available publications while you build your profile."
                : data.mode === "hybrid"
                  ? "Based on your skills, interests and observed community feedback."
                  : "Based on your skills and interests. When details are missing, available publications help you get started."}
            </p>
            <section className="panel">
              <div className="section-title">
                <h2>
                  <BriefcaseBusiness size={20} />
                  Opportunities to explore
                </h2>
              </div>
              {rows(data.listings, "listing")}
            </section>
            <section className="panel review-panel">
              <div className="section-title">
                <h2>
                  <BookOpen size={20} />
                  Learning resources
                </h2>
              </div>
              {rows(data.content, "content")}
            </section>
          </>
        )
      )}
    </>
  );
}
