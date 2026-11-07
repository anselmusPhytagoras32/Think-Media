import { ThinkIcon } from "./brand";
import { Artwork } from "./artwork";
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
  Send,
  Sparkles,
} from "lucide-react";
import { api, manila } from "./api";
import { SuggestionsPreview } from "./suggestions-preview";
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
    [result, setResult] = useState<{ correct: number; total: number } | null>(
      null,
    ),
    [reporting, setReporting] = useState(false),
    [resolving, setResolving] = useState<Report | null>(null),
    [addQuiz, setAddQuiz] = useState(false);
  const [detailRevision, setDetailRevision] = useState(0);
  const sequence = useRef(0);
  useEffect(
    () => () => {
      sequence.current++;
    },
    [],
  );
  async function load() {
    const current = ++sequence.current;
    setBusy(true);
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
      else setItems(d.items as Content[]);
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
        await api<{ correct: number; total: number }>(
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
      <header className="page-heading">
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
                : "Build workplace confidence with approved preparation resources."}
          </p>
        </div>
        {admin && !reports && (
          <button
            className="primary"
            onClick={() => {
              setEditing("new");
              setSelected(null);
              setAddQuiz(false);
              setError("");
              setSuccess("");
            }}
          >
            <Plus size={17} />
            New resource
          </button>
        )}
      </header>
      <Messages error={error} success={success} />
      {editing ? (
        <section className="panel" key={editing === "new" ? "new" : editing.id}>
          <div className="detail-toolbar">
            <h2>
              {editing === "new"
                ? "Create a learning resource"
                : "Edit learning resource"}
            </h2>
            <button className="secondary" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </div>
          <form onSubmit={saveContent}>
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
            <button className="primary" disabled={busy}>
              {busy ? "Saving…" : "Save resource"}
            </button>
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
            Back to resources
          </button>
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
                </form>
              )}
            </>
          )}
        </section>
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
                setFilter("&" + p.toString());
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
                    ? "No reports to review"
                    : admin
                      ? "No learning resources yet"
                      : "No resources found"}
                </h3>
                <p>
                  {reports
                    ? "Reported content will appear here for review."
                    : admin
                      ? "Create a draft to prepare your first approved resource."
                      : "Try another topic or check again when resources are published."}
                </p>
              </div>
            ) : reports ? (
              reportItems.map((r) => (
                <article className="company-row" key={r.id}>
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
                    <Artwork
                      kind={item.has_quiz ? "applications" : "learning"}
                    />
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
              <h2>Resolve content report</h2>
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
function Satisfaction() {
  const [value, setValue] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [saved, setSaved] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/feedback/csat", "POST", { rating: Number(value) });
      setSaved(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="satisfaction-form" onSubmit={submit}>
      <h3>Was this guidance helpful?</h3>
      <p className="muted">
        This optional satisfaction rating helps improve guidance. It does not
        affect your applications.
      </p>
      <div className="field">
        <label htmlFor="guidance-satisfaction">
          Helpfulness rating (optional)
        </label>
        <select
          id="guidance-satisfaction"
          required
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setSaved(false);
          }}
        >
          <option value="">Choose a rating</option>
          <option value="1">1 · Very unhelpful</option>
          <option value="2">2 · Unhelpful</option>
          <option value="3">3 · Neutral</option>
          <option value="4">4 · Helpful</option>
          <option value="5">5 · Very helpful</option>
        </select>
      </div>
      <button className="secondary" disabled={busy || !value}>
        Share satisfaction rating
      </button>
      {saved && (
        <p className="rating-saved" role="status">
          Thank you. Your satisfaction rating was saved.
        </p>
      )}
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
export function Assistant() {
  const [sourceContent, setSourceContent] = useState<Content | null>(null);
  const [question, setQuestion] = useState(""),
    [answer, setAnswer] = useState<{
      answer: string;
      sources: { id: string; title: string }[];
      uncertainty: string | boolean;
      mode: string;
    } | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function ask(e?: FormEvent) {
    e?.preventDefault();
    if (!question.trim()) return;
    setBusy(true);
    setError("");
    setAnswer(null);
    setSourceContent(null);
    try {
      setAnswer(await api("/assistant", "POST", { question }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <header className="page-heading">
        <div>
          <h1>OJT preparation guidance</h1>
          <p>
            Explore career and platform questions using approved learning
            resources.
          </p>
        </div>
      </header>
      <section className="assistant-panel panel">
        <div className="assistant-intro">
          <BookOpen size={28} />
          <h2>Ask about preparing for OJT</h2>
          <p>
            Ask about OJT preparation, workplace skills or using ThinkMedia.
            Guidance supports your preparation; companies make application
            decisions.
          </p>
        </div>
        <p className="privacy">
          Keep personal details, resumes and private application information out
          of your question.
        </p>
        <form onSubmit={ask}>
          <div className="field">
            <label htmlFor="assistant-question">Your question</label>
            <textarea
              id="assistant-question"
              required
              maxLength={2000}
              rows={4}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="How can I prepare for an OJT interview?"
            />
          </div>
          <button className="primary" disabled={busy || !question.trim()}>
            {busy ? "Looking for guidance…" : "Ask for guidance"}
            <Send size={16} />
          </button>
        </form>
        {busy && (
          <p className="muted" role="status">
            Checking approved resources…
          </p>
        )}
        <Messages error={error} />
        {error && (
          <div className="assistant-recovery">
            <p>Your applications and opportunities remain available.</p>
            <button
              className="secondary"
              disabled={busy}
              onClick={() => void ask()}
            >
              Try again
            </button>
          </div>
        )}
        {answer && (
          <section className="assistant-answer">
            <span className="badge">
              {answer.mode === "retrieval"
                ? "Approved resource lookup"
                : "Grounded guidance"}
            </span>
            <h2>Guidance from your resources</h2>
            <p className="preserve-lines">{answer.answer}</p>
            {answer.uncertainty && (
              <p className="notice">
                {typeof answer.uncertainty === "string"
                  ? answer.uncertainty
                  : "The available resources may not fully answer your question."}
              </p>
            )}
            <h3>Sources</h3>
            {answer.sources.length ? (
              <ul>
                {answer.sources.map((source) => (
                  <li key={source.id}>
                    <button
                      className="text-button"
                      onClick={async () => {
                        try {
                          setSourceContent(
                            await api<Content>(`/content/${source.id}`),
                          );
                        } catch (e) {
                          setError((e as Error).message);
                        }
                      }}
                    >
                      {source.title}
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">No matching approved sources were found.</p>
            )}
            <Satisfaction />
            {sourceContent && (
              <article className="source-preview">
                <h3>{sourceContent.title}</h3>
                <p className="preserve-lines">{sourceContent.body}</p>
              </article>
            )}
          </section>
        )}
      </section>
    </>
  );
}
