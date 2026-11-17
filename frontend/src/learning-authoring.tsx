// FR03/11: private authoring and administrator review of learning submissions.
import { type FormEvent, useEffect, useRef, useState } from "react";
import { BookOpen, Plus } from "lucide-react";
import { api, ApiError, manila } from "./api";
import { useDataRevision } from "./live-data";
import { href } from "./navigation";
import "./learning-authoring.css";

type Kind = "lesson" | "skill";
type Status = "draft" | "pending" | "changes_requested" | "approved";
type Page<T> = { items: T[]; total: number };
type Skill = { id: string; name: string };
type Link = { label: string; url: string };
type Question = { question: string; options: string[]; correct_index: number; feedback: string | null };
type Lesson = {
  kind: "lesson";
  title: string;
  summary: string;
  body: string;
  tags: string[];
  skill_ids: string[];
  links: Link[];
  questions: Question[];
};
type Draft = Lesson | { kind: "skill"; title: string; summary: string };
type Summary = {
  id: string;
  kind: Kind;
  title: string;
  summary: string;
  status: Status;
  version: number;
  updated_at: string;
};
type Submission = Summary & {
  draft: Draft;
  skills: Skill[];
  attachment_name: string | null;
  published_content_id: string | null;
  review: { feedback: string; reviewed_at: string } | null;
};
const statusLabel: Record<Status, string> = {
  draft: "Draft",
  pending: "Awaiting review",
  changes_requested: "Changes requested",
  approved: "Approved",
};
const pageSize = 20;
const emptyQuestion = (): Question => ({ question: "", options: ["", ""], correct_index: 0, feedback: null });

function Fields({ draft }: { draft?: Draft }) {
  const lesson = draft?.kind === "lesson" ? draft : undefined;
  const [links, setLinks] = useState(lesson?.links ?? []);
  const [questions, setQuestions] = useState(lesson?.questions ?? []);
  const changeQuestion = (index: number, value: Question) =>
    setQuestions((current) => current.map((item, i) => i === index ? value : item));

  return (
    <>
      <fieldset className="authoring-group">
        <legend>Reference links</legend>
        {links.map((link, index) => (
          <div className="authoring-fields" key={index}>
            <label className="field">Link {index + 1} label
              <input name="link_label" required maxLength={200} value={link.label}
                onChange={(e) => setLinks((items) => items.map((item, i) => i === index ? { ...item, label: e.target.value } : item))} />
            </label>
            <label className="field">Link {index + 1} URL
              <input name="link_url" required type="url" maxLength={2048} value={link.url}
                onChange={(e) => setLinks((items) => items.map((item, i) => i === index ? { ...item, url: e.target.value } : item))} />
            </label>
            <button type="button" className="text-button" onClick={() => setLinks((items) => items.filter((_, i) => i !== index))}>
              Remove link {index + 1}
            </button>
          </div>
        ))}
        {links.length < 10 && (
          <button type="button" className="secondary" onClick={() => setLinks((items) => [...items, { label: "", url: "" }])}>
            Add a reference link
          </button>
        )}
      </fieldset>
      <fieldset className="authoring-group">
        <legend>Quiz</legend>
        {questions.map((item, index) => (
          <fieldset className="authoring-group" key={index}>
            <legend>Question {index + 1}</legend>
            <label className="field">Question text
              <input name={"question-" + index} required maxLength={1000} value={item.question}
                onChange={(e) => changeQuestion(index, { ...item, question: e.target.value })} />
            </label>
            {item.options.map((option, optionIndex) => (
              <label className="field" key={optionIndex}>Option {optionIndex + 1}
                <input name={"option-" + index} required maxLength={1000} value={option}
                  onChange={(e) => changeQuestion(index, {
                    ...item, options: item.options.map((text, i) => i === optionIndex ? e.target.value : text),
                  })} />
              </label>
            ))}
            <div className="authoring-actions">
              {item.options.length < 6 && (
                <button type="button" className="text-button" onClick={() => changeQuestion(index, { ...item, options: [...item.options, ""] })}>
                  Add option
                </button>
              )}
              {item.options.length > 2 && (
                <button type="button" className="text-button" onClick={() => changeQuestion(index, {
                  ...item, options: item.options.slice(0, -1),
                  correct_index: Math.min(item.correct_index, item.options.length - 2),
                })}>
                  Remove last option
                </button>
              )}
            </div>
            <label className="field">Correct option
              <select name={"correct-" + index} value={item.correct_index}
                onChange={(e) => changeQuestion(index, { ...item, correct_index: Number(e.target.value) })}>
                {item.options.map((_, i) => <option value={i} key={i}>Option {i + 1}</option>)}
              </select>
            </label>
            <label className="field">Feedback after submission
              <textarea name={"feedback-" + index} maxLength={1000} rows={2} value={item.feedback ?? ""}
                onChange={(e) => changeQuestion(index, { ...item, feedback: e.target.value })} />
            </label>
            <button type="button" className="text-button" onClick={() => setQuestions((items) => items.filter((_, i) => i !== index))}>
              Remove question {index + 1}
            </button>
          </fieldset>
        ))}
        {questions.length < 20 && (
          <button type="button" className="secondary" onClick={() => setQuestions((items) => [...items, emptyQuestion()])}>
            Add a quiz question
          </button>
        )}
      </fieldset>
    </>
  );
}

function SkillPicker({ initial }: { initial: Skill[] }) {
  const [selected, setSelected] = useState(initial);
  const [items, setItems] = useState<Skill[]>([]);
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(true);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    setBusy(true);
    setError("");
    const params = new URLSearchParams({ q: query, offset: String(offset), limit: "10" });
    api<Page<Skill>>("/learning-skills?" + params)
      .then((page) => { if (active) { setItems(page.items); setTotal(page.total); } })
      .catch((failure) => { if (active) setError(failure.message); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [offset, query, retry]);
  return (
    <fieldset className="authoring-group">
      <legend>Approved skill categories</legend>
      <label className="field">Find a skill category
        <input type="search" maxLength={80} value={query}
          onChange={(e) => { setQuery(e.target.value); setOffset(0); }} />
      </label>
      {selected.length > 0 && (
        <ul className="authoring-inline-list">
          {selected.map((item) => (
            <li key={item.id}>
              <input type="hidden" name="skill_id" value={item.id} />
              <button type="button" className="secondary"
                onClick={() => setSelected((current) => current.filter((skill) => skill.id !== item.id))}>
                Remove {item.name}
              </button>
            </li>
          ))}
        </ul>
      )}
      {busy ? <p role="status">Loading skill categories…</p> : error ? (
        <div role="alert">{error} <button className="text-button" type="button" onClick={() => setRetry((n) => n + 1)}>Retry</button></div>
      ) : items.length ? (
        <ul className="authoring-inline-list">
          {items.map((item) => (
            <li key={item.id}>
              <button type="button" className="secondary"
                disabled={selected.length >= 30 || selected.some((skill) => skill.id === item.id)}
                onClick={() => setSelected((current) => [...current, item])}>
                Add {item.name}
              </button>
            </li>
          ))}
        </ul>
      ) : <p>No approved skill categories match this search.</p>}
      {!busy && !error && total > 10 && (
        <div className="authoring-actions">
          <button type="button" className="secondary" disabled={!offset} onClick={() => setOffset(offset - 10)}>Previous skills</button>
          <button type="button" className="secondary" disabled={offset + 10 >= total} onClick={() => setOffset(offset + 10)}>Next skills</button>
        </div>
      )}
    </fieldset>
  );
}

function makeDraft(data: FormData, kind: Kind): Draft {
  const read = (key: string) => String(data.get(key) ?? "").trim();
  const title = read("title"), summary = read("summary");
  if (kind === "skill") return { kind, title, summary };
  const labels = data.getAll("link_label").map(String);
  const urls = data.getAll("link_url").map(String);
  const questions: Question[] = [];
  for (let i = 0; data.has("question-" + i); i++) {
    questions.push({
      question: read("question-" + i),
      options: data.getAll("option-" + i).map(String),
      correct_index: Number(read("correct-" + i)),
      feedback: read("feedback-" + i) || null,
    });
  }
  return {
    kind, title, summary, body: read("body"),
    tags: [...new Set(read("tags").split(",").map((value) => value.trim()).filter(Boolean))],
    skill_ids: data.getAll("skill_id").map(String),
    links: labels.map((label, i) => ({ label, url: urls[i] })),
    questions,
  };
}

function DraftForm({ kind, selected, busy, onSave }: {
  kind: Kind;
  selected: Submission | null;
  busy: boolean;
  onSave: (payload: FormData) => void;
}) {
  const draft = selected?.draft;
  const lesson = draft?.kind === "lesson" ? draft : undefined;
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const payload = new FormData();
    payload.set("draft", JSON.stringify(makeDraft(data, kind)));
    const file = data.get("file");
    if (file instanceof File && file.name) payload.set("file", file);
    if (selected) payload.set("expected_version", String(selected.version));
    if (data.has("remove_attachment")) payload.set("remove_attachment", "true");
    onSave(payload);
  }
  return (
    <form onSubmit={submit}>
      <fieldset disabled={busy} className="authoring-controls">
        <label className="field">{kind === "lesson" ? "Lesson title" : "Skill name"}
          <input name="title" required maxLength={kind === "lesson" ? 200 : 80} defaultValue={draft?.title} />
        </label>
        <label className="field">{kind === "lesson" ? "Summary" : "Description"}
          <textarea name="summary" required maxLength={500} rows={3} defaultValue={draft?.summary} />
        </label>
        {kind === "lesson" && (
          <>
            <label className="field">Lesson text
              <textarea name="body" required maxLength={20000} rows={8} defaultValue={lesson?.body} />
            </label>
            <label className="field">Tags (comma-separated)
              <input name="tags" maxLength={2500} defaultValue={lesson?.tags.join(", ")} />
            </label>
            <SkillPicker initial={selected?.skills ?? []} />
            <div className="authoring-group">
              <label className="field">PDF attachment (up to 5 MiB)
                <input name="file" type="file" accept="application/pdf,.pdf" />
              </label>
              {selected?.attachment_name && (
                <label><input type="checkbox" name="remove_attachment" /> Remove {selected.attachment_name}</label>
              )}
            </div>
            <Fields draft={draft} />
          </>
        )}
        <button className="primary" type="submit">{busy ? "Saving…" : "Save draft"}</button>
      </fieldset>
    </form>
  );
}

export function ResourceMaterials({ links, attachment, path }: { links: Link[]; attachment?: string | null; path: string }) {
  if (!links.length && !attachment) return null;
  return (
    <section className="authoring-materials" aria-label="Lesson materials">
      <h3>Materials</h3>
      <ul>
        {links.map((link, i) => <li key={i}><a href={link.url} target="_blank" rel="noopener noreferrer">{link.label}</a></li>)}
        {attachment && <li><a href={"/api/v1" + path + "/attachment"} download>Download {attachment}</a></li>}
      </ul>
    </section>
  );
}

export function LearningAuthoring({ admin, initialId, onSelect }: {
  admin: boolean;
  initialId?: string;
  onSelect: (id?: string) => void;
}) {
  const path = admin ? "/admin/learning-submissions" : "/instructor/learning";
  const [items, setItems] = useState<Summary[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState<Status>("pending");
  const [selected, setSelected] = useState<Submission | null>(null);
  const [editing, setEditing] = useState<Kind | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [confirmation, setConfirmation] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const live = useDataRevision(["learning"], !initialId && !editing);
  const heading = useRef<HTMLHeadingElement>(null);
  const confirmButton = useRef<HTMLButtonElement>(null);
  const detailPath = initialId ? path + "/" + initialId : path;

  useEffect(() => {
    if (initialId || editing) return;
    let active = true;
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ offset: String(offset), limit: String(pageSize) });
    if (admin) params.set("status", status);
    api<Page<Summary>>(path + "?" + params)
      .then((data) => { if (active) { setItems(data.items); setTotal(data.total); } })
      .catch((failure) => { if (active) setError(failure.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [admin, path, initialId, editing, offset, status, revision, live]);
  useEffect(() => {
    setEditing(null);
    setSelected(null);
    setConfirmation(null);
    if (!initialId) return;
    let active = true;
    setLoading(true);
    setError("");
    api<Submission>(detailPath)
      .then((item) => { if (active) setSelected(item); })
      .catch((failure) => { if (active) setError(failure.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [initialId, detailPath, revision]);
  useEffect(() => { if (editing || selected) heading.current?.focus(); }, [editing, selected?.id]);
  useEffect(() => { if (confirmation !== null) confirmButton.current?.focus(); }, [confirmation]);

  async function mutate(url: string, method: string, payload: unknown, message: string) {
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const updated = await api<Submission>(url, method, payload);
      setSelected(updated);
      setEditing(null);
      setConfirmation(null);
      setSuccess(message);
      if (!initialId) onSelect(updated.id);
    } catch (failure) {
      const conflict = failure instanceof ApiError && failure.status === 409;
      const details = failure instanceof ApiError ? Object.values(failure.fields).flat().join(" ") : "";
      setError([conflict && editing ? "Your draft is still open." : "", (failure as Error).message, details].filter(Boolean).join(" "));
    } finally {
      setSaving(false);
    }
  }

  function review(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const data = new FormData(event.currentTarget, (event.nativeEvent as SubmitEvent).submitter);
    const decision = data.get("decision");
    if (!decision) return;
    if (decision === "approved") {
      setError("");
      setConfirmation(String(data.get("feedback") ?? ""));
      return;
    }
    void mutate(detailPath, "PATCH", {
      decision, feedback: String(data.get("feedback") ?? ""), expected_version: selected.version,
    }, "Changes requested.");
  }

  function back() {
    setEditing(null);
    setError("");
    setSuccess("");
    onSelect();
  }

  const editable = selected?.status === "draft" || selected?.status === "changes_requested";
  const current = selected?.id === initialId ? selected : null;

  return (
    <div className="learning-authoring">
      <header className="page-heading role-page-heading">
        <div>
          <h1>{admin ? "Learning review" : "Teaching materials"}</h1>
          <p>{admin ? "Review instructor lessons and skill categories before publication." :
            "Draft lessons and propose skill categories for the Learning Library."}</p>
        </div>
        {!admin && !initialId && !editing && (
          <div className="authoring-actions">
            <button className="primary" onClick={() => setEditing("lesson")}><Plus size={17} aria-hidden="true" /> New lesson</button>
            <button className="secondary" onClick={() => setEditing("skill")}>New skill category</button>
          </div>
        )}
        {admin && <a className="secondary" href={href("content")}>Back to learning content</a>}
      </header>
      {error && (
        <div role="alert" className="notice error">
          <span>{error}</span>{" "}
          {(!current || error.includes("Reopen it")) && !editing && (
            <button className="text-button" onClick={() => setRevision((n) => n + 1)}>Reload</button>
          )}
        </div>
      )}
      {success && <div className="notice success" role="status">{success}</div>}
      {editing ? (
        <section className="panel">
          <div className="detail-toolbar">
            <h2 ref={heading} tabIndex={-1}>{current ? "Edit draft" : editing === "lesson" ? "New lesson" : "New skill category"}</h2>
            <button className="secondary" disabled={saving} onClick={() => { setEditing(null); setError(""); }}>Cancel</button>
          </div>
          <DraftForm kind={editing} selected={current} busy={saving}
            onSave={(payload) => void mutate(detailPath, current ? "PUT" : "POST", payload, "Draft saved.")} />
        </section>
      ) : initialId ? (
        <section className="panel">
          <button className="text-button" disabled={saving} onClick={back}>Back to {admin ? "review queue" : "my materials"}</button>
          {loading && <p role="status">Loading submission…</p>}
          {current && (
            <>
              <div className="detail-toolbar">
                <h2 ref={heading} tabIndex={-1}>{current.title}</h2>
                <span className="authoring-status">{statusLabel[current.status]}</span>
              </div>
              <p>{current.summary}</p>
              {current.review?.feedback && (
                <section aria-label="Administrator feedback">
                  <h3>Administrator feedback</h3>
                  <p className="preserve-lines">{current.review.feedback}</p>
                </section>
              )}
              {current.draft.kind === "lesson" && (
                <>
                  <p className="preserve-lines">{current.draft.body}</p>
                  {(current.skills.length > 0 || current.draft.tags.length > 0) && (
                    <p><strong>Topics:</strong> {[...current.skills.map((skill) => skill.name), ...current.draft.tags].join(", ")}</p>
                  )}
                  <ResourceMaterials links={current.draft.links} attachment={current.attachment_name} path={detailPath} />
                  {current.draft.questions.length > 0 && (
                    <section>
                      <h3>Quiz preview</h3>
                      <ol className="authoring-quiz-preview">
                        {current.draft.questions.map((item, index) => (
                          <li key={index}>
                            <strong>{item.question}</strong>
                            <ul>{item.options.map((option, i) => <li key={i}>{option}{i === item.correct_index && " (correct)"}</li>)}</ul>
                            {item.feedback && <p>{item.feedback}</p>}
                          </li>
                        ))}
                      </ol>
                    </section>
                  )}
                </>
              )}
              {current.published_content_id && (
                <p><a href={href(admin ? "content" : "learning", current.published_content_id)}>View lesson in the library</a></p>
              )}
              {!admin && editable && (
                <div className="authoring-actions">
                  <button className="secondary" disabled={saving} onClick={() => { setEditing(current.kind); setError(""); setSuccess(""); }}>Edit draft</button>
                  <button className="primary" disabled={saving} onClick={() => void mutate(
                    detailPath + "/submit", "POST", { expected_version: current.version }, "Submitted for administrator review.",
                  )}>Submit for review</button>
                </div>
              )}
              {admin && current.status === "pending" && (
                <form className="authoring-group" onSubmit={review}>
                  <fieldset className="authoring-controls" disabled={saving || confirmation !== null}>
                    <label className="field">Review feedback
                      <textarea name="feedback" rows={3} maxLength={1000} aria-describedby="learning-review-help" />
                    </label>
                    <p id="learning-review-help">Feedback is required when requesting changes.</p>
                    <div className="authoring-actions">
                      <button className="secondary" type="submit" name="decision" value="changes_requested">Request changes</button>
                      <button className="primary" type="submit" name="decision" value="approved">Approve and publish</button>
                    </div>
                  </fieldset>
                </form>
              )}
              {confirmation !== null && current.status === "pending" && (
                <section className="authoring-group" aria-label="Confirm publication">
                  <p>Publish {current.title} in the {current.kind === "lesson" ? "Learning Library" : "skill catalog"}?</p>
                  <div className="authoring-actions">
                    <button className="secondary" disabled={saving} onClick={() => setConfirmation(null)}>Cancel</button>
                    <button ref={confirmButton} className="primary" disabled={saving} onClick={() => void mutate(
                      detailPath, "PATCH",
                      { decision: "approved", feedback: confirmation, expected_version: current.version },
                      "Submission approved and published.",
                    )}>Confirm publication</button>
                  </div>
                </section>
              )}
            </>
          )}
        </section>
      ) : (
        <section className="panel">
          <h2>{admin ? "Review queue" : "My submissions"}</h2>
          {admin && (
            <label className="field authoring-filter">Review status
              <select value={status} onChange={(event) => { setStatus(event.target.value as Status); setOffset(0); }}>
                <option value="pending">Awaiting review</option>
                <option value="changes_requested">Changes requested</option>
                <option value="approved">Approved</option>
              </select>
            </label>
          )}
          {loading && <p role="status">Loading submissions…</p>}
          {!loading && !error && items.length === 0 && <p>{admin ? "No submissions match this status." : "Create a lesson or skill category to get started."}</p>}
          {!error && items.length > 0 && (
            <ul className="authoring-list">
              {items.map((item) => (
                <li key={item.id}>
                  <BookOpen size={20} aria-hidden="true" />
                  <div>
                    <button className="text-button" onClick={() => { setSuccess(""); onSelect(item.id); }}>{item.title}</button>
                    <p>{item.kind === "lesson" ? "Lesson" : "Skill category"} · {manila(item.updated_at)}</p>
                  </div>
                  <span className="authoring-status">{statusLabel[item.status]}</span>
                </li>
              ))}
            </ul>
          )}
          {total > pageSize && (
            <div className="authoring-actions">
              <button className="secondary" disabled={loading || !offset} onClick={() => setOffset(offset - pageSize)}>Previous</button>
              <button className="secondary" disabled={loading || offset + pageSize >= total} onClick={() => setOffset(offset + pageSize)}>Next</button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
