// FR08/09; NFR05/09: real suggestions with opt-in relevance feedback.
import { FormEvent, useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  BriefcaseBusiness,
  Check,
  ChevronDown,
  MapPin,
  RefreshCw,
  Sparkles,
  UserRound,
} from "lucide-react";
import { Account, api } from "./api";
import { suggestionReason } from "./copy";
import { Marketplace } from "./marketplace";
import { Learning } from "./learning";
import { CompanyLogo } from "./company-brand";
import { ResourceArtwork } from "./resource-artwork";
import { href } from "./navigation";
type Item = {
  id: string;
  title: string;
  company_id?: string;
  company_name?: string;
  location?: string;
  type?: "ojt" | "job";
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
type View = "all" | "listing" | "content";
function Rating({ item, kind }: { item: Item; kind: "listing" | "content" }) {
  const [expanded, setExpanded] = useState(false),
    [rating, setRating] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [success, setSuccess] = useState("");
  const formId = "rating-form-" + kind + "-" + item.id;
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy || !rating) return;
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
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="suggestion-rating">
      <button
        type="button"
        className="suggestion-rate-toggle"
        disabled={busy}
        aria-expanded={expanded}
        aria-controls={formId}
        onClick={() => setExpanded(!expanded)}
      >
        Rate relevance <ChevronDown size={14} />
      </button>
      <div id={formId} hidden={!expanded}>
        <form className="rating-form" onSubmit={submit}>
          <div className="field">
            <label htmlFor={"rating-" + kind + "-" + item.id}>
              Relevance rating (optional)
            </label>
            <select
              id={"rating-" + kind + "-" + item.id}
              required
              disabled={busy}
              value={rating}
              onChange={(event) => {
                setRating(event.target.value);
                setSuccess("");
                setError("");
              }}
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
      </div>
    </div>
  );
}
function Mode({ mode }: { mode: Suggestions["mode"] }) {
  return (
    <p className="suggestion-mode">
      <Sparkles size={16} />
      {mode === "general"
        ? "A starting point from available opportunities and resources. Add profile details for more relevant suggestions."
        : mode === "hybrid"
          ? "Based on your skills, interests and observed community feedback."
          : "Based on your skills and interests."}
    </p>
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
    [view, setView] = useState<View>("all"),
    [target, setTarget] = useState<{
      kind: "listing" | "content";
      id: string;
    } | null>(null);
  const request = useRef(0);
  async function load() {
    const current = ++request.current;
    setBusy(true);
    setError("");
    setData(null);
    try {
      const response = await api<Suggestions>("/recommendations?limit=10");
      if (current === request.current) setData(response);
    } catch (failure) {
      if (current === request.current) setError((failure as Error).message);
    } finally {
      if (current === request.current) setBusy(false);
    }
  }
  useEffect(() => {
    void load();
    return () => {
      request.current++;
    };
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
  const section = (items: Suggestion[], kind: "listing" | "content") => (
    <section
      className={"suggestions-section suggestions-" + kind}
      aria-labelledby={"suggestions-" + kind + "-title"}
    >
      <div className="suggestions-section-heading">
        <h2 id={"suggestions-" + kind + "-title"}>
          {kind === "listing" ? (
            <BriefcaseBusiness size={20} />
          ) : (
            <BookOpen size={20} />
          )}
          {kind === "listing"
            ? "Opportunities to explore"
            : "Learning resources"}
        </h2>
        <a href={href(kind === "listing" ? "opportunities" : "learning")}>
          {kind === "listing" ? "Browse opportunities" : "Browse resources"}
          <ArrowRight size={15} />
        </a>
      </div>
      {items.length ? (
        <div className="suggestions-card-grid">
          {items.map(({ item, reason }) => (
            <article
              className={
                "suggestion-row suggestion-card suggestion-card-" + kind
              }
              key={kind + ":" + item.id}
            >
              {kind === "content" && (
                <button
                  type="button"
                  className="suggestion-card-art"
                  onClick={() => open(kind, item.id)}
                  aria-label={"Read " + item.title}
                >
                  <ResourceArtwork title={item.title} tags={item.tags || []} />
                </button>
              )}
              <div className="suggestion-content">
                {kind === "listing" && (
                  <div className="suggestion-company">
                    {item.company_id && item.company_name && (
                      <CompanyLogo
                        companyId={item.company_id}
                        companyName={item.company_name}
                      />
                    )}
                    <div>
                      {item.company_name && (
                        <p className="company-name">{item.company_name}</p>
                      )}
                      <span>
                        {item.type === "ojt"
                          ? "OJT placement"
                          : item.type === "job"
                            ? "Job opportunity"
                            : "Opportunity"}
                      </span>
                    </div>
                  </div>
                )}
                <h3>
                  <button type="button" onClick={() => open(kind, item.id)}>
                    {item.title}
                  </button>
                </h3>
                {kind === "listing" && item.location && (
                  <p className="suggestion-location">
                    <MapPin size={14} />
                    {item.location}
                  </p>
                )}
                <p className="suggestion-summary">
                  {(item.summary || item.description || "").slice(0, 190)}
                  {(item.summary || item.description || "").length > 190
                    ? "…"
                    : ""}
                </p>
                {!!(item.skills || item.tags)?.length && (
                  <ul
                    className="suggestion-tags"
                    aria-label={
                      kind === "listing" ? "Related skills" : "Resource topics"
                    }
                  >
                    {(item.skills || item.tags || []).slice(0, 4).map((tag) => (
                      <li key={tag}>{tag}</li>
                    ))}
                  </ul>
                )}
                <p className="suggestion-reason">
                  <Sparkles size={14} />
                  {suggestionReason(reason)}
                </p>
                <button
                  type="button"
                  className="text-button suggestion-open"
                  onClick={() => open(kind, item.id)}
                >
                  {kind === "listing" ? "View opportunity" : "Read resource"}
                  <ArrowRight size={15} />
                </button>
              </div>
              <Rating item={item} kind={kind} />
            </article>
          ))}
        </div>
      ) : (
        <div className="suggestions-empty">
          <h3>
            {kind === "listing"
              ? "No opportunities to suggest yet"
              : "No resources to suggest yet"}
          </h3>
          <p>
            Check the wider catalog or update your profile while new items are
            published.
          </p>
          <a
            className="secondary"
            href={href(kind === "listing" ? "opportunities" : "learning")}
          >
            {kind === "listing"
              ? "Browse all opportunities"
              : "Explore the learning library"}
            <ArrowRight size={15} />
          </a>
        </div>
      )}
    </section>
  );
  return (
    <div className="suggestions-page">
      <header className="page-heading suggestions-heading">
        <div>
          <h1>Suggestions for you</h1>
          <p>Explore opportunities and learning resources in one place.</p>
        </div>
        <button
          className="secondary"
          aria-label="Refresh"
          title="Refresh suggestions"
          disabled={busy}
          onClick={() => void load()}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </header>
      <div className="suggestions-layout">
        <div className="suggestions-main">
          <div
            className="suggestions-view-switch"
            role="group"
            aria-label="Suggestion categories"
          >
            {(
              [
                ["all", "All suggestions"],
                ["listing", "Opportunities"],
                ["content", "Learning"],
              ] as const
            ).map(([key, label]) => (
              <button
                type="button"
                key={key}
                aria-pressed={view === key}
                onClick={() => setView(key)}
              >
                {label}
              </button>
            ))}
          </div>
          {busy ? (
            <p className="suggestions-state" role="status">
              Finding eligible suggestions…
            </p>
          ) : error ? (
            <section
              className="suggestions-state suggestions-error"
              role="alert"
            >
              <h2>Suggestions are unavailable</h2>
              <p>{error}</p>
              <p>Try again or keep exploring the catalog.</p>
              <div>
                <button className="primary" onClick={() => void load()}>
                  Try again
                </button>
                <a className="secondary" href={href("opportunities")}>
                  Browse opportunities
                </a>
              </div>
            </section>
          ) : (
            data && (
              <>
                <Mode mode={data.mode} />
                {view !== "content" && section(data.listings, "listing")}
                {view !== "listing" && section(data.content, "content")}
              </>
            )
          )}
        </div>
        <aside
          className="suggestions-profile"
          aria-labelledby="suggestions-profile-title"
        >
          <div className="suggestions-profile-icon">
            <UserRound size={22} />
          </div>
          <h2 id="suggestions-profile-title">Shape your next step</h2>
          <p>
            {account.profile.skills?.length
              ? "Keep your skills and goals current so suggestions can reflect your interests."
              : "Add a few skills and interests to give suggestions a useful starting point."}
          </p>
          {!!account.profile.skills?.length && (
            <div className="suggestions-profile-skills">
              {account.profile.skills.slice(0, 4).map((skill) => (
                <span key={skill}>{skill}</span>
              ))}
            </div>
          )}
          <button type="button" className="text-button" onClick={onProfile}>
            Update your skills and interests <ArrowRight size={15} />
          </button>
          <p className="suggestions-note">
            Suggestions support exploration. Companies make application
            decisions. Ratings are optional and do not affect your applications.
          </p>
        </aside>
      </div>
    </div>
  );
}
