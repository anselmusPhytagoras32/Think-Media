import { ThinkIcon } from "./brand";
import { Artwork } from "./artwork";
import { ResourceArtwork } from "./resource-artwork";
import { useDataRevision } from "./live-data";
// FR03/10/11 / NFR02–03,05,09–11: published resources, moderation and bounded guidance.
import { FormEvent, useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Bookmark,
  Check,
  Flag,
  Heart,
  Plus,
  Sparkles,
  Search,
} from "lucide-react";
import { api, manila } from "./api";
import { SuggestionsPreview } from "./suggestions-preview";
import { ResourceMaterials } from "./learning-authoring";
import { href } from "./navigation";
type Content = {
  id: string;
  title: string;
  summary: string;
  body: string;
  tags: string[];
  status: "draft" | "published" | "archived";
  has_quiz: boolean;
  saved: boolean;
  reacted: boolean;
  created_at: string;
  updated_at: string;
  links?: { label: string; url: string }[];
  attachment_name?: string | null;
};
type Report = {
  id: string;
  content_id: string;
  reason: string;
  status: "pending" | "resolved";
  created_at: string;
  resolution?: string;
};
type Question = { id: string; question: string; options: string[] };
type QuizResult = { correct: number; total: number; feedback?: { question_id: string; text: string }[] };
type Page<T> = { items: T[]; total: number; limit: number; offset: number };
function Messages({ error, success }: { error: string; success?: string }) {
  return (
    <>
      {error && (
        <div className="notice error" role="alert">
          {error}
        </div>
      )}
      {success && (
        <div className="notice success" role="status">
          <Check size={18} />
          {success}
        </div>
      )}
    </>
  );
}
// FR03/08, NFR05/09: the real library leads; suggestions are an optional view.
function LearningLibrary({
  items,
  total,
  offset,
  busy,
  error,
  filter,
  topics,
  skillTopics,
  personalized,
  view,
  onView,
  onFilter,
  onOpen,
  onFeedback,
  onPage,
  onRetry,
}: {
  items: Content[];
  total: number;
  offset: number;
  busy: boolean;
  error: string;
  filter: string;
  topics: string[];
  skillTopics: string[];
  personalized: boolean;
  view: "all" | "suggested";
  onView: (view: "all" | "suggested") => void;
  onFilter: (value: string) => void;
  onOpen: (item: Pick<Content, "id">) => void;
  onFeedback: (item: Content, kind: "save" | "react") => void;
  onPage: (offset: number) => void;
  onRetry: () => void;
}) {
  const params = new URLSearchParams(filter);
  const activeTopic = params.get("tag") || "";
  return (
    <div className="learning-library">
      <form
        className="library-search"
        role="search"
        aria-label="Learning library"
        onSubmit={(event) => {
          event.preventDefault();
          const search = new URLSearchParams();
          for (const [key, value] of new FormData(event.currentTarget))
            if (String(value).trim()) search.set(key, String(value).trim());
          onView("all");
          onFilter(search.toString());
        }}
      >
        <div className="field library-keyword">
          <label htmlFor="resource-search">Search resources</label>
          <div>
            <Search size={18} aria-hidden="true" />
            <input
              id="resource-search"
              name="q"
              defaultValue={params.get("q") || ""}
              placeholder="What would you like to learn?"
            />
          </div>
        </div>
        <div className="field library-topic-field">
          <label htmlFor="resource-tag">Topic</label>
          <input
            id="resource-tag"
            name="tag"
            defaultValue={activeTopic}
            placeholder="Any topic"
            list={skillTopics.length ? "learning-skill-categories" : undefined}
          />
          {skillTopics.length > 0 && (
            <datalist id="learning-skill-categories">
              {skillTopics.map((name) => <option key={name} value={name} />)}
            </datalist>
          )}
        </div>
        <button className="primary" disabled={busy}>
          Search <ArrowRight size={16} />
        </button>
      </form>
      {!!topics.length && (
        <div
          className="library-topics"
          role="group"
          aria-label="Explore learning topics"
        >
          <span>Explore topics</span>
          {topics.map((topic) => (
            <button
              key={topic}
              type="button"
              aria-label={`Explore ${topic}`}
              aria-pressed={
                activeTopic.toLocaleLowerCase() === topic.toLocaleLowerCase()
              }
              disabled={busy}
              onClick={() => {
                const next = new URLSearchParams(filter);
                if (
                  activeTopic.toLocaleLowerCase() === topic.toLocaleLowerCase()
                )
                  next.delete("tag");
                else next.set("tag", topic);
                onView("all");
                onFilter(next.toString());
              }}
            >
              {topic}
            </button>
          ))}
        </div>
      )}
      <div className="library-views" role="group" aria-label="Learning views">
        <button
          type="button"
          aria-pressed={view === "all"}
          onClick={() => onView("all")}
        >
          All resources
        </button>
        {personalized && (
          <button
            type="button"
            aria-pressed={view === "suggested"}
            onClick={() => onView("suggested")}
          >
            For you <Sparkles size={15} />
          </button>
        )}
      </div>
      {view === "suggested" ? (
        <section
          className="library-suggestions"
          aria-label="Suggested learning"
        >
          <SuggestionsPreview
            kind="content"
            onOpen={(id) => onOpen({ id })}
            browseHint="Choose All resources to keep exploring the library."
          />
          <button
            type="button"
            className="secondary"
            onClick={() => onView("all")}
          >
            Browse all resources
          </button>
        </section>
      ) : (
        <>
          <div className="library-results-heading">
            <h2>
              {activeTopic ? `${activeTopic} resources` : "Explore the library"}
            </h2>
            <span role="status">
              {busy
                ? "Updating resources…"
                : `${total} ${total === 1 ? "resource" : "resources"}`}
            </span>
            {filter && (
              <button
                type="button"
                className="text-button"
                onClick={() => onFilter("")}
              >
                Clear filters
              </button>
            )}
          </div>
          {error ? (
            <div className="library-state">
              <p>
                Resources could not be loaded. Try again to continue learning.
              </p>
              <button type="button" className="secondary" onClick={onRetry}>
                Retry loading
              </button>
            </div>
          ) : (
            <>
              {busy && !items.length && (
                <p className="library-state" role="status">
                  Loading resources…
                </p>
              )}
              {!busy && total === 0 && (
                <div className="empty library-state">
                  <BookOpen size={32} />
                  <h3>No resources found</h3>
                  <p>Try a broader search or choose another topic.</p>
                  {filter && (
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => onFilter("")}
                    >
                      Browse all resources
                    </button>
                  )}
                </div>
              )}
              <div className="library-resource-grid" aria-busy={busy}>
                {items.map((item) => (
                  <article
                    className="resource-row library-resource-card"
                    key={item.id}
                  >
                    <button
                      type="button"
                      className="library-resource-visual"
                      disabled={busy}
                      onClick={() => onOpen(item)}
                      aria-label={`${item.has_quiz ? "Guide & quiz" : "Guide"}: Read ${item.title}`}
                    >
                      <ResourceArtwork title={item.title} tags={item.tags} />
                      <span className="library-resource-kind">
                        <BookOpen size={13} />
                        {item.has_quiz ? "Guide & quiz" : "Guide"}
                      </span>
                    </button>
                    <div className="library-resource-copy">
                      <div className="library-resource-topics">
                        {item.tags.slice(0, 3).map((tag) => (
                          <span key={tag}>{tag}</span>
                        ))}
                      </div>
                      <h3>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => onOpen(item)}
                        >
                          {item.title}
                        </button>
                      </h3>
                      <p>{item.summary}</p>
                      <div className="feed-actions">
                        <button
                          type="button"
                          className="text-button"
                          disabled={busy}
                          onClick={() => onOpen(item)}
                        >
                          Read resource <ArrowRight size={15} />
                        </button>
                        <button
                          type="button"
                          className="secondary library-feedback"
                          aria-label={`${item.saved ? "Saved; remove saved resource" : "Save"} ${item.title}`}
                          aria-pressed={item.saved}
                          disabled={busy}
                          onClick={() => onFeedback(item, "save")}
                        >
                          <Bookmark size={16} />
                          <span>{item.saved ? "Saved" : "Save"}</span>
                        </button>
                        <button
                          type="button"
                          className="secondary library-feedback"
                          aria-label={`${item.reacted ? "Reacted; remove reaction to" : "React to"} ${item.title}`}
                          aria-pressed={item.reacted}
                          disabled={busy}
                          onClick={() => onFeedback(item, "react")}
                        >
                          <Heart size={16} />
                          <span>{item.reacted ? "Reacted" : "React"}</span>
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
              <div className="pagination library-pagination">
                <button
                  disabled={busy || !offset}
                  onClick={() => onPage(offset - 20)}
                >
                  Previous
                </button>
                <span>
                  {total
                    ? `${offset + 1}–${Math.min(total, offset + 20)} of ${total}`
                    : "0 results"}
                </span>
                <button
                  disabled={busy || offset + 20 >= total}
                  onClick={() => onPage(offset + 20)}
                >
                  Next
                </button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
export function Learning({
  admin = false,
  reports = false,
  initialId,
  personalized = false,
  onSelect,
}: {
  admin?: boolean;
  reports?: boolean;
  initialId?: string;
  personalized?: boolean;
  onSelect?: (id?: string) => void;
}) {
  const [items, setItems] = useState<Content[]>([]),
    [reportItems, setReportItems] = useState<Report[]>([]),
    [selected, setSelected] = useState<Content | null>(null),
    [editing, setEditing] = useState<Content | "new" | null>(null),
    [offset, setOffset] = useState(0),
    [total, setTotal] = useState(0),
    [filter, setFilter] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [success, setSuccess] = useState(""),
    [quiz, setQuiz] = useState<Question[] | null>(null),
    [result, setResult] = useState<QuizResult | null>(null),
    [reporting, setReporting] = useState(false),
    [resolving, setResolving] = useState<Report | null>(null),
    [addQuiz, setAddQuiz] = useState(false);
  const [detailRevision, setDetailRevision] = useState(0);
  const [catalogTopics, setCatalogTopics] = useState<string[]>([]);
  const [skillTopics, setSkillTopics] = useState<string[]>([]);
  const [libraryView, setLibraryView] = useState<"all" | "suggested">("all");
  // FR11/W08: publication requires a separate review before the API mutation.
  const [pendingPublication, setPendingPublication] = useState<Record<
    string,
    unknown
  > | null>(null);
  const publicationHeading = useRef<HTMLHeadingElement>(null);
  const resolutionHeading = useRef<HTMLHeadingElement>(null);
  const editorHeading = useRef<HTMLHeadingElement>(null);
  const liveRevision = useDataRevision(["learning"], !editing && !pendingPublication && !resolving && !quiz && !reporting);
  useEffect(() => {
    if (pendingPublication) publicationHeading.current?.focus();
  }, [pendingPublication]);
  useEffect(() => { if (resolving) resolutionHeading.current?.focus(); }, [resolving]);
  useEffect(() => { if (editing) editorHeading.current?.focus(); }, [editing]);
  const sequence = useRef(0);
  useEffect(() => {
    if (admin || reports) return;
    let active = true;
    api<Page<{ name: string }>>("/learning-skills?limit=100")
      .then((data) => { if (active) setSkillTopics(data.items.map((skill) => skill.name)); })
      .catch(() => { if (active) setSkillTopics([]); });
    return () => { active = false; };
  }, [admin, reports, liveRevision]);
  useEffect(
    () => () => {
      sequence.current++;
    },
    [],
  );
  async function load(background = false) {
    const current = ++sequence.current;
    if (!background) setBusy(true);
    setError("");
    try {
      const path = reports
        ? "/admin/reports"
        : admin
          ? "/admin/content"
          : "/content";
      const d = await api<Page<Content | Report>>(
        `${path}?limit=20&offset=${offset}${filter}`,
      );
      if (current !== sequence.current) return;
      if (reports) setReportItems(d.items as Report[]);
      else {
        const content = d.items as Content[];
        setItems(content);
        if (!admin && !filter && offset === 0)
          setCatalogTopics(
            [...new Set(content.flatMap((item) => item.tags))]
              .sort((a, b) => a.localeCompare(b))
              .slice(0, 6),
          );
      }
      setTotal(d.total);
    } catch (e) {
      if (current === sequence.current) setError((e as Error).message);
    } finally {
      if (current === sequence.current) setBusy(false);
    }
  }
  useEffect(() => {
    void load();
  }, [offset, filter]);
  useEffect(() => {
    if (!liveRevision) return;
    let active = true;
    void load(true);
    if (selected) api<Content>(`/content/${selected.id}`)
      .then((fresh) => { if (active) setSelected(fresh); })
      .catch((failure) => { if (active) { setSelected(null); setError(failure.message); } });
    return () => { active = false; };
  }, [liveRevision]);
  useEffect(() => {
    setSelected(null);
    setQuiz(null);
    setResult(null);
    setReporting(false);
    setError("");
    if (!initialId) {
      setSelected(null);
      setQuiz(null);
      return;
    }
    let active = true;
    setBusy(true);
    api<Content>(`/content/${initialId}`)
      .then((item) => {
        if (active) setSelected(item);
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [initialId, detailRevision]);
  async function open(item: Pick<Content, "id">) {
    setBusy(true);
    setError("");
    setSuccess("");
    setQuiz(null);
    setResult(null);
    setReporting(false);
    try {
      const resource = await api<Content>(`/content/${item.id}`);
      setSelected(resource);
      onSelect?.(resource.id);
      if (!admin)
        void api("/interactions", "POST", {
          item_type: "content",
          item_id: resource.id,
          event_type: "view",
        }).catch(() => {});
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function feedback(item: Content, kind: "save" | "react") {
    setBusy(true);
    setError("");
    try {
      await api(
        `/content/${item.id}/${kind}`,
        "POST",
        kind === "save" ? { saved: !item.saved } : { reacted: !item.reacted },
      );
      const updated = await api<Content>(`/content/${item.id}`);
      setItems((old) => old.map((c) => (c.id === item.id ? updated : c)));
      if (selected?.id === item.id) setSelected(updated);
      setSuccess(
        kind === "save"
          ? updated.saved
            ? "Resource saved."
            : "Resource removed from saved items."
          : updated.reacted
            ? "Reaction added."
            : "Reaction removed.",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function takeQuiz() {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      const data = await api<{ questions: Question[] }>(
        `/content/${selected.id}/quiz`,
      );
      setQuiz(data.questions);
      setResult(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function submitQuiz(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selected) return;
    const answers = Object.fromEntries(
      [...new FormData(e.currentTarget)].map(([k, v]) => [k, Number(v)]),
    );
    setBusy(true);
    setError("");
    try {
      setResult(
        await api<QuizResult>(
          `/content/${selected.id}/quiz`,
          "POST",
          { answers },
        ),
      );
      setSuccess("Your quiz result has been recorded.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function saveContent(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const d = Object.fromEntries(new FormData(e.currentTarget));
    const payload: Record<string, unknown> = {
      title: d.title,
      summary: d.summary,
      body: d.body,
      tags: String(d.tags)
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      status: d.status,
    };
    if (editing === "new" && addQuiz)
      payload.questions = [
        {
          question: d.question,
          options: [d.option0, d.option1, d.option2, d.option3].filter(Boolean),
          correct_index: Number(d.correct_index),
        },
      ];
    if (
      payload.status === "published" &&
      (editing === "new" || editing?.status !== "published")
    ) {
      setPendingPublication(payload);
      return;
    }
    await persistContent(payload);
  }
  async function persistContent(payload: Record<string, unknown>) {
    setBusy(true);
    setError("");
    try {
      const saved = await api<Content>(
        editing === "new"
          ? "/admin/content"
          : `/admin/content/${(editing as Content).id}`,
        editing === "new" ? "POST" : "PATCH",
        payload,
      );
      setEditing(null);
      setPendingPublication(null);
      setSelected(saved);
      onSelect?.(saved.id);
      setSuccess("Learning resource saved.");
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function report(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selected) return;
    const form = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      await api("/reports", "POST", {
        content_id: selected.id,
        reason: form.get("reason"),
      });
      setReporting(false);
      setSuccess("Report submitted for administrator review.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function resolve(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!resolving) return;
    const form = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      await api(`/admin/reports/${resolving.id}`, "PATCH", {
        status: "resolved",
        resolution: form.get("resolution"),
      });
      setResolving(null);
      setSuccess("Report resolution recorded.");
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <header
        className={`page-heading ${!admin && !reports && !selected ? "learning-library-hero" : ""} ${admin || reports ? "role-page-heading" : ""}`}
      >
        <div>
          <h1>
            {reports
              ? "Content reports"
              : admin
                ? "Learning content"
                : "Learning resources"}
          </h1>
          <p>
            {reports
              ? "Review concerns and record a moderation decision."
              : admin
                ? "Prepare, review and publish trusted career resources."
                : "Read a guide. Try a skill. Take your next step toward OJT."}
          </p>
        </div>
        {!admin && !reports && !selected && (
          <Artwork kind="learning" className="learning-hero-art" priority />
        )}
        {admin && !reports && !editing && (
          <div className="authoring-actions">
            <a className="secondary" href={href("learning-review")}>Review instructor submissions</a>
            <button
              className="primary"
              onClick={() => {
                setEditing("new");
                setPendingPublication(null);
                setSelected(null);
                setAddQuiz(false);
                setError("");
                setSuccess("");
              }}
            >
              <Plus size={17} />
              New resource
            </button>
          </div>
        )}
      </header>
      <Messages error={error} success={success} />
      {editing ? (
        <section className="panel" key={editing === "new" ? "new" : editing.id}>
          <div className="detail-toolbar">
            <h2 ref={editorHeading} tabIndex={-1}>
              {editing === "new"
                ? "Create a learning resource"
                : "Edit learning resource"}
            </h2>
            <button
              className="secondary"
              onClick={() => {
                setEditing(null);
                setPendingPublication(null);
              }}
            >
              Cancel
            </button>
          </div>
          <form
            onSubmit={saveContent}
            onChange={() => setPendingPublication(null)}
          >
            <div className="field">
              <label htmlFor="content-title">Title (required)</label>
              <input
                id="content-title"
                name="title"
                required
                maxLength={200}
                defaultValue={editing === "new" ? "" : editing.title}
              />
            </div>
            <div className="field">
              <label htmlFor="content-summary">Summary (required)</label>
              <textarea
                id="content-summary"
                name="summary"
                required
                maxLength={500}
                rows={3}
                defaultValue={editing === "new" ? "" : editing.summary}
              />
            </div>
            <div className="field">
              <label htmlFor="content-body">Resource text (required)</label>
              <textarea
                id="content-body"
                name="body"
                required
                maxLength={20000}
                rows={10}
                defaultValue={editing === "new" ? "" : editing.body}
              />
            </div>
            <div className="field">
              <label htmlFor="content-tags">
                Topics (separate with commas)
              </label>
              <input
                id="content-tags"
                name="tags"
                maxLength={2500}
                defaultValue={editing === "new" ? "" : editing.tags.join(", ")}
              />
            </div>
            <div className="field">
              <label htmlFor="content-status">Publication status</label>
              <select
                id="content-status"
                name="status"
                defaultValue={editing === "new" ? "draft" : editing.status}
              >
                <option value="draft">Draft</option>
                <option value="published">Published</option>
                {editing !== "new" && (
                  <option value="archived">Archived</option>
                )}
              </select>
            </div>
            {editing === "new" && (
              <>
                <label className="check-label">
                  <input
                    type="checkbox"
                    checked={addQuiz}
                    onChange={(e) => setAddQuiz(e.target.checked)}
                  />
                  Include a short quiz
                </label>
                {addQuiz && (
                  <fieldset className="quiz-editor">
                    <legend>Quiz question</legend>
                    <div className="field">
                      <label htmlFor="quiz-question">Question (required)</label>
                      <input
                        id="quiz-question"
                        name="question"
                        required
                        maxLength={1000}
                      />
                    </div>
                    {[0, 1, 2, 3].map((i) => (
                      <div className="field" key={i}>
                        <label htmlFor={`option${i}`}>
                          Answer option {i + 1}
                          (required)
                        </label>
                        <input
                          id={`option${i}`}
                          name={`option${i}`}
                          required
                          maxLength={500}
                        />
                      </div>
                    ))}
                    <div className="field">
                      <label htmlFor="correct-option">
                        Correct answer option
                      </label>
                      <select id="correct-option" name="correct_index">
                        <option value="0">Option 1</option>
                        <option value="1">Option 2</option>
                        <option value="2">Option 3</option>
                        <option value="3">Option 4</option>
                      </select>
                    </div>
                  </fieldset>
                )}
              </>
            )}
            <p className="privacy">
              Published resources become available to learners and grounded
              guidance. Check the text and answer key before publishing.
            </p>
            {pendingPublication && (
              <section
                className="confirmation"
                aria-labelledby="publication-review-title"
              >
                <h3
                  id="publication-review-title"
                  tabIndex={-1}
                  ref={publicationHeading}
                >
                  Review publication
                </h3>
                <p>
                  Publish <strong>{String(pendingPublication.title)}</strong>?
                  Learners will be able to read this resource and guidance can
                  cite it. Check the resource and quiz answer key before
                  confirming.
                </p>
                <div className="actions">
                  <button
                    type="button"
                    className="secondary"
                    disabled={busy}
                    onClick={() => {
                      setPendingPublication(null);
                      document.getElementById("content-title")?.focus();
                    }}
                  >
                    Keep editing
                  </button>
                  <button
                    type="button"
                    className="primary"
                    disabled={busy}
                    onClick={() => void persistContent(pendingPublication)}
                  >
                    Confirm publication
                  </button>
                </div>
              </section>
            )}
            {!pendingPublication && (
              <button className="primary" disabled={busy}>
                {busy ? "Saving…" : "Save resource"}
              </button>
            )}
          </form>
        </section>
      ) : selected ? (
        <section className="panel learning-detail">
          <button
            className="back-button"
            onClick={() => {
              setSelected(null);
              onSelect?.(undefined);
              setQuiz(null);
              setSuccess("");
              setError("");
            }}
          >
            <ArrowLeft size={16} />
            Back to {reports ? "reports" : "resources"}
          </button>
          {!admin && (
            <ResourceArtwork
              title={selected.title}
              tags={selected.tags}
              className="library-detail-art"
              priority
            />
          )}
          <div className="detail-toolbar">
            <h2>{selected.title}</h2>
            {admin && <span className="badge">{selected.status}</span>}
          </div>
          <div className="listing-meta">
            {selected.tags.map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
          <p className="resource-summary">{selected.summary}</p>
          <div className="resource-body preserve-lines">{selected.body}</div>
          <ResourceMaterials links={selected.links ?? []} attachment={selected.attachment_name} path={"/content/" + selected.id} />
          {admin ? (
            <button className="primary" onClick={() => setEditing(selected)}>
              Edit resource
            </button>
          ) : (
            <>
              <div className="learning-actions">
                <button
                  className="secondary"
                  disabled={busy}
                  aria-pressed={selected.saved}
                  onClick={() => feedback(selected, "save")}
                >
                  <Bookmark size={16} />
                  {selected.saved ? "Saved" : "Save resource"}
                </button>
                <button
                  className="secondary"
                  disabled={busy}
                  aria-pressed={selected.reacted}
                  onClick={() => feedback(selected, "react")}
                >
                  <Heart size={16} />
                  {selected.reacted ? "Reacted" : "React"}
                </button>
                {selected.has_quiz && (
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={takeQuiz}
                  >
                    Open quiz
                  </button>
                )}
                <button
                  className="text-button"
                  onClick={() => setReporting(!reporting)}
                >
                  <Flag size={15} />
                  Report resource
                </button>
              </div>
              {reporting && (
                <form className="apply-form" onSubmit={report}>
                  <div className="field">
                    <label htmlFor="report-reason">
                      What needs attention? (required)
                    </label>
                    <textarea
                      id="report-reason"
                      name="reason"
                      required
                      maxLength={1000}
                      rows={3}
                    />
                  </div>
                  <button className="primary" disabled={busy}>
                    Submit report
                  </button>
                </form>
              )}
              {quiz && (
                <form className="quiz-form" onSubmit={submitQuiz}>
                  <h3>Check your understanding</h3>
                  {quiz.map((q) => (
                    <fieldset key={q.id}>
                      <legend>{q.question}</legend>
                      {q.options.map((option, i) => (
                        <label className="radio-label" key={i}>
                          <input type="radio" required name={q.id} value={i} />
                          {option}
                        </label>
                      ))}
                    </fieldset>
                  ))}
                  {quiz.length > 0 ? (
                    <button className="primary" disabled={busy}>
                      Submit answers
                    </button>
                  ) : (
                    <p>No quiz is available for this resource.</p>
                  )}
                  {result && (
                    <p className="quiz-result" role="status">
                      You answered {result.correct} of {result.total} correctly.
                    </p>
                  )}
                  {result?.feedback?.length ? (
                    <section aria-label="Quiz feedback">
                      <h3>Quiz feedback</h3>
                      <ul>{result.feedback.map((item) => <li key={item.question_id}>{item.text}</li>)}</ul>
                    </section>
                  ) : null}
                </form>
              )}
            </>
          )}
        </section>
      ) : !admin && !reports ? (
        <LearningLibrary
          key={filter}
          items={items}
          total={total}
          offset={offset}
          busy={busy}
          error={error}
          filter={filter}
            topics={catalogTopics}
            skillTopics={skillTopics}
          personalized={personalized}
          view={libraryView}
          onView={setLibraryView}
          onFilter={(value) => {
            setLibraryView("all");
            setOffset(0);
            setFilter(value ? "&" + value : "");
          }}
          onOpen={(item) => void open(item)}
          onFeedback={(item, kind) => void feedback(item, kind)}
          onPage={setOffset}
          onRetry={() =>
            initialId ? setDetailRevision((n) => n + 1) : void load()
          }
        />
      ) : (
        <>
          {!reports && (
            <form
              className="learning-search"
              onSubmit={(e) => {
                e.preventDefault();
                const d = new FormData(e.currentTarget);
                const p = new URLSearchParams();
                for (const [k, v] of d) if (v) p.set(k, String(v));
                setOffset(0);
                setFilter(p.size ? "&" + p.toString() : "");
              }}
            >
              <div className="field">
                <label htmlFor="resource-search">Search resources</label>
                <input
                  id="resource-search"
                  name="q"
                  defaultValue={new URLSearchParams(filter).get("q") || ""}
                  placeholder="Interview tips, workplace skills…"
                />
              </div>
              <div className="field">
                <label htmlFor="resource-tag">Topic</label>
                <input
                  id="resource-tag"
                  name="tag"
                  defaultValue={new URLSearchParams(filter).get("tag") || ""}
                  placeholder="Any topic"
                />
              </div>
              {admin && (
                <div className="field">
                  <label htmlFor="resource-filter-status">Status</label>
                  <select
                    id="resource-filter-status"
                    name="status"
                    defaultValue={
                      new URLSearchParams(filter).get("status") || ""
                    }
                  >
                    <option value="">All statuses</option>
                    <option value="draft">Draft</option>
                    <option value="published">Published</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              )}
              <button className="primary" disabled={busy}>
                Search
              </button>
            </form>
          )}
          {personalized && !admin && !reports && (
            <SuggestionsPreview
              kind="content"
              onOpen={(id) => void open({ id })}
            />
          )}
          <section className="panel">
            {reports && (
              <div className="field">
                <label htmlFor="report-status">Report status</label>
                <select
                  id="report-status"
                  value={new URLSearchParams(filter).get("status") || "pending"}
                  onChange={(e) => {
                    setOffset(0);
                    setResolving(null);
                    setFilter("&status=" + e.target.value);
                  }}
                >
                  <option value="pending">Pending</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>
            )}
            {busy ? (
              <p role="status">Loading…</p>
            ) : error ? (
              <button
                className="secondary"
                onClick={() =>
                  initialId ? setDetailRevision((n) => n + 1) : void load()
                }
              >
                Retry loading
              </button>
            ) : total === 0 ? (
              <div className="empty">
                <BookOpen size={32} />
                <h3>
                  {reports
                    ? new URLSearchParams(filter).get("status") === "resolved" ? "No resolved reports" : "No reports to review"
                    : admin && !filter
                      ? "No learning resources yet"
                      : "No resources found"}
                </h3>
                <p>
                  {reports
                    ? new URLSearchParams(filter).get("status") === "resolved" ? "Resolved reports will appear here." : "Reported content will appear here for review."
                    : admin && !filter
                      ? "Create a draft to prepare your first approved resource."
                      : "Try another topic or check again when resources are published."}
                </p>
              </div>
            ) : reports ? (
              reportItems.map((r) => (
                <article className="company-row report-row" key={r.id}>
                  <span className="role-row-icon" aria-hidden="true"><Flag size={21} /></span>
                  <div>
                    <h3>Content report</h3>
                    <p>{r.reason}</p>
                    <small>{manila(r.created_at)}</small>
                    {r.resolution && <p>Resolution: {r.resolution}</p>}
                  </div>
                  {r.status === "pending" ? (
                    <button
                      className="secondary"
                      onClick={() => setResolving(r)}
                    >
                      Review report
                    </button>
                  ) : (
                    <span className="badge">Resolved</span>
                  )}
                </article>
              ))
            ) : (
              items.map((item) => (
                <article className="resource-row" key={item.id}>
                  <div className="resource-artwork-cover" aria-hidden="true">
                    <ResourceArtwork title={item.title} tags={item.tags} />
                  </div>
                  <div className="detail-toolbar">
                    <h2>
                      <button onClick={() => open(item)}>{item.title}</button>
                    </h2>
                    {admin && <span className="badge">{item.status}</span>}
                  </div>
                  <div className="listing-meta">
                    {item.has_quiz && <span>Includes a quiz</span>}
                    {item.tags.map((tag) => (
                      <span key={tag}>{tag}</span>
                    ))}
                  </div>
                  <p>{item.summary}</p>
                  <div className="feed-actions">
                    <button className="text-button" onClick={() => open(item)}>
                      Read resource
                      <ArrowRight size={15} />
                    </button>
                    {!admin && (
                      <>
                        <button
                          className="secondary"
                          aria-label={`${item.saved ? "Saved; remove saved resource" : "Save"} ${item.title}`}
                          aria-pressed={item.saved}
                          disabled={busy}
                          onClick={() => feedback(item, "save")}
                        >
                          <Bookmark size={15} />
                          {item.saved ? "Saved" : "Save"}
                        </button>
                        <button
                          className="secondary"
                          aria-label={`${item.reacted ? "Reacted; remove reaction to" : "React to"} ${item.title}`}
                          aria-pressed={item.reacted}
                          disabled={busy}
                          onClick={() => feedback(item, "react")}
                        >
                          <Heart size={15} />
                          {item.reacted ? "Reacted" : "React"}
                        </button>
                      </>
                    )}
                  </div>
                </article>
              ))
            )}
            <div className="pagination">
              <button
                disabled={busy || !offset}
                onClick={() => setOffset(offset - 20)}
              >
                Previous
              </button>
              <span>
                {total
                  ? `${offset + 1}–${Math.min(total, offset + 20)} of ${total}`
                  : "0 results"}
              </span>
              <button
                disabled={busy || offset + 20 >= total}
                onClick={() => setOffset(offset + 20)}
              >
                Next
              </button>
            </div>
          </section>
          {resolving && (
            <section className="panel review-panel">
              <h2 ref={resolutionHeading} tabIndex={-1}>Resolve content report</h2>
              <p>{resolving.reason}</p>
              <button
                className="secondary"
                disabled={busy}
                onClick={async () => {
                  try {
                    setSelected(
                      await api<Content>(`/content/${resolving.content_id}`),
                    );
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                Inspect reported resource
              </button>
              <form onSubmit={resolve}>
                <div className="field">
                  <label htmlFor="resolution">Resolution (required)</label>
                  <textarea
                    id="resolution"
                    name="resolution"
                    required
                    maxLength={1000}
                    rows={3}
                  />
                </div>
                <div className="actions">
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => setResolving(null)}
                  >
                    Cancel
                  </button>
                  <button className="primary" disabled={busy}>
                    Confirm resolution
                  </button>
                </div>
              </form>
            </section>
          )}
        </>
      )}
    </>
  );
}
