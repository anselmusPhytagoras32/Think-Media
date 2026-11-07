// FR04–07 / NFR02–05,09–11: live marketplace workflows; no synthetic results.
import { useEffect, useState, useRef, FormEvent } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  Check,
  Download,
  MapPin,
  Plus,
  Search,
} from "lucide-react";
import { api, Account, manila } from "./api";
import { SuggestionsPreview } from "./suggestions-preview";
import { StatusBadge } from "./status";
import { ThinkIcon } from "./brand";
import { Artwork } from "./artwork";
import { href } from "./navigation";
export type Listing = {
  id: string;
  company_id: string;
  company_name: string;
  title: string;
  description: string;
  requirements: string;
  location: string;
  type: "ojt" | "job";
  skills: string[];
  status: "draft" | "published" | "closed";
  created_at: string;
  updated_at: string;
  company_description?: string;
  company_website?: string;
};
export type Application = {
  id: string;
  reference: string;
  listing_id: string;
  listing_title: string;
  company_name: string;
  student_id: string;
  student_name: string;
  status: "submitted" | "under_review" | "accepted" | "rejected";
  cover_letter: string;
  attachment_name: string;
  created_at: string;
  history: {
    actor_id: string;
    old_status: string | null;
    new_status: string;
    created_at: string;
  }[];
  student_profile?: {
    institution: string;
    program: string;
    skills: string[];
    interests: string[];
    location: string;
    background: string;
  };
};
type List<T> = { items: T[]; total: number; limit: number; offset: number };
const statusLabel = (s: string) => s.replaceAll("_", " ");
function Feedback({ error, success }: { error: string; success?: string }) {
  return (
    <>
      {error && (
        <div role="alert" className="notice error">
          {error}
        </div>
      )}
      {success && (
        <div role="status" className="notice success">
          <Check size={18} />
          {success}
        </div>
      )}
    </>
  );
}
function Input({
  name,
  label,
  value,
  kind = "input",
  required = false,
  maxLength = 200,
}: {
  name: string;
  label: string;
  value?: string;
  kind?: string;
  required?: boolean;
  maxLength?: number;
}) {
  return (
    <div className="field">
      <label htmlFor={`market-${name}`}>
        {label}
        {required ? " (required)" : ""}
      </label>
      {kind === "textarea" ? (
        <textarea
          id={`market-${name}`}
          name={name}
          defaultValue={value}
          required={required}
          maxLength={maxLength}
          rows={5}
        />
      ) : (
        <input
          id={`market-${name}`}
          name={name}
          defaultValue={value}
          required={required}
          maxLength={maxLength}
        />
      )}
    </div>
  );
}
function Pager({
  offset,
  total,
  busy,
  onChange,
}: {
  offset: number;
  total: number;
  busy: boolean;
  onChange: (n: number) => void;
}) {
  return (
    <div className="pagination">
      <button
        disabled={offset === 0 || busy}
        onClick={() => onChange(offset - 20)}
      >
        Previous
      </button>
      <span>
        {total
          ? `${offset + 1}–${Math.min(total, offset + 20)} of ${total}`
          : "0 results"}
      </span>
      <button
        disabled={offset + 20 >= total || busy}
        onClick={() => onChange(offset + 20)}
      >
        Next
      </button>
    </div>
  );
}
function Tags({ listing: l }: { listing: Listing }) {
  return (
    <div className="listing-meta">
      <span>{l.type === "ojt" ? "OJT" : "Job"}</span>
      <span>
        <MapPin size={14} />
        {l.location}
      </span>
      {l.skills.map((s) => (
        <span key={s}>{s}</span>
      ))}
    </div>
  );
}
export function Marketplace({
  account,
  mode,
  initialId,
  initialApplicationId,
  initialFilters = "",
  onFilters,
  onListing,
  onApplication,
}: {
  account: Account;
  initialId?: string;
  initialApplicationId?: string;
  initialFilters?: string;
  onFilters?: (filters: string) => void;
  onListing?: (id?: string) => void;
  onApplication?: (id?: string) => void;
  mode: "browse" | "company" | "applications" | "review";
}) {
  const [items, setItems] = useState<Listing[]>([]),
    [apps, setApps] = useState<Application[]>([]),
    [total, setTotal] = useState(0),
    [offset, setOffset] = useState(0),
    [filters, setFilters] = useState(
      initialFilters ? "&" + initialFilters : "",
    ),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [success, setSuccess] = useState(""),
    [selected, setSelected] = useState<Listing | null>(null),
    [application, setApplication] = useState<Application | null>(null),
    [editing, setEditing] = useState<Listing | "new" | null>(null),
    [applying, setApplying] = useState(false),
    [confirm, setConfirm] = useState(false),
    [decision, setDecision] = useState(""),
    [pendingAction, setPendingAction] = useState<"publish" | "close" | null>(
      null,
    );
  const [detailRevision, setDetailRevision] = useState(0);
  const [reviewFile, setReviewFile] = useState<File | null>(null),
    [reviewLetter, setReviewLetter] = useState("");
  const loadSequence = useRef(0);
  useEffect(() => {
    setFilters(initialFilters ? "&" + initialFilters : "");
    setOffset(0);
  }, [initialFilters]);
  useEffect(
    () => () => {
      loadSequence.current++;
    },
    [],
  );
  const company = mode === "company",
    applicationMode = mode === "applications" || mode === "review";
  async function load() {
    const sequence = ++loadSequence.current;
    setBusy(true);
    setError("");
    try {
      if (applicationMode) {
        const d = await api<List<Application>>(
          `${mode === "review" ? "/company/applications" : "/applications/me"}?limit=20&offset=${offset}`,
        );
        if (sequence !== loadSequence.current) return;
        setApps(d.items);
        setTotal(d.total);
      } else {
        const d = await api<List<Listing>>(
          `${company ? "/company/listings" : "/listings"}?limit=20&offset=${offset}${filters}`,
        );
        if (sequence !== loadSequence.current) return;
        setItems(d.items);
        setTotal(d.total);
      }
    } catch (e) {
      if (sequence === loadSequence.current) setError((e as Error).message);
    } finally {
      if (sequence === loadSequence.current) setBusy(false);
    }
  }
  useEffect(() => {
    setSelected(null);
    setApplication(null);
    setEditing(null);
    setApplying(false);
    setConfirm(false);
    setSuccess("");
    setOffset(0);
  }, [mode]);
  useEffect(() => {
    void load();
  }, [mode, offset, filters]);
  useEffect(() => {
    setSelected(null);
    setApplying(false);
    setConfirm(false);
    setReviewFile(null);
    setReviewLetter("");
    setEditing(null);
    setPendingAction(null);
    setError("");
    if (!initialId) {
      setSelected(null);
      return;
    }
    let active = true;
    setBusy(true);
    api<Listing>(`/listings/${initialId}`)
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
  useEffect(() => {
    setApplication(null);
    setDecision("");
    setError("");
    if (!initialApplicationId) {
      setApplication(null);
      return;
    }
    let active = true;
    setBusy(true);
    api<Application>(`/applications/${initialApplicationId}`)
      .then((item) => {
        if (active) setApplication(item);
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
  }, [initialApplicationId, detailRevision]);
  async function open(l: Pick<Listing, "id">) {
    setBusy(true);
    setError("");
    setSuccess("");
    setApplying(false);
    setConfirm(false);
    setPendingAction(null);
    try {
      const item = await api<Listing>(`/listings/${l.id}`);
      setSelected(item);
      onListing?.(item.id);
      if (
        ["student", "instructor"].includes(account.user.role) &&
        item.status === "published"
      )
        void api("/interactions", "POST", {
          item_type: "listing",
          item_id: item.id,
          event_type: "view",
        }).catch(() => {});
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function search(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const params = new URLSearchParams();
    for (const [k, v] of new FormData(e.currentTarget))
      if (v) params.set(k, String(v));
    setOffset(0);
    setFilters(params.size ? "&" + params.toString() : "");
    onFilters?.(params.toString());
  }
  async function saveListing(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget));
    setBusy(true);
    setError("");
    try {
      const result = await api<Listing>(
        editing === "new"
          ? "/company/listings"
          : `/company/listings/${(editing as Listing).id}`,
        editing === "new" ? "POST" : "PATCH",
        {
          ...data,
          skills: String(data.skills)
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
        },
      );
      setEditing(null);
      setSelected(result);
      onListing?.(result.id);
      setSuccess("Listing saved. Publish the draft when it is ready.");
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function transition() {
    if (!selected || !pendingAction) return;
    setBusy(true);
    setError("");
    try {
      setSelected(
        await api<Listing>(
          `/company/listings/${selected.id}/${pendingAction}`,
          "POST",
        ),
      );
      setSuccess(
        pendingAction === "publish"
          ? "Your opportunity is now published."
          : "Listing closed. Existing applications are preserved.",
      );
      setPendingAction(null);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function submitApplication(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selected) return;
    const form = new FormData(e.currentTarget);
    const file = form.get("file");
    if (
      !(file instanceof File) ||
      !file.size ||
      file.size > 5 * 1024 * 1024 ||
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      setError("Attach a PDF up to 5 MiB before confirming.");
      setConfirm(false);
      return;
    }
    if (!confirm) {
      setError("");
      setReviewFile(file);
      setReviewLetter(String(form.get("cover_letter") || ""));
      setConfirm(true);
      return;
    }
    setBusy(true);
    setError("");
    try {
      const receipt = await api<Application>(
        `/listings/${selected.id}/applications`,
        "POST",
        form,
      );
      setApplication(receipt);
      setSelected(null);
      setApplying(false);
      setSuccess(`Application submitted. Reference: ${receipt.reference}`);
      onApplication?.(receipt.id);
    } catch (e) {
      setError((e as Error).message);
      setConfirm(false);
    } finally {
      setBusy(false);
    }
  }
  async function viewApplication(a: Application) {
    setBusy(true);
    setError("");
    try {
      setApplication(await api<Application>(`/applications/${a.id}`));
      onApplication?.(a.id);
      setDecision("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function decide(e: FormEvent) {
    e.preventDefault();
    if (!application || !decision) return;
    setBusy(true);
    setError("");
    try {
      setApplication(
        await api<Application>(
          `/applications/${application.id}/status`,
          "PATCH",
          { status: decision },
        ),
      );
      setDecision("");
      setSuccess("Application status updated and recorded in history.");
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const title =
    mode === "browse"
      ? "OJT and job opportunities"
      : company
        ? "Your opportunities"
        : mode === "review"
          ? "Review applicants"
          : "My applications";
  return (
    <>
      <header className="page-heading">
        <div>
          <h1>{title}</h1>
          <p>
            {mode === "browse"
              ? "Explore published opportunities from verified companies."
              : company
                ? "Create, publish and manage your organization’s listings."
                : mode === "review"
                  ? "Review submissions to your listings and record decisions."
                  : "Follow your submissions, references and status history."}
          </p>
        </div>
        {company && (
          <button
            className="primary"
            onClick={() => {
              setEditing("new");
              setSelected(null);
              setError("");
              setSuccess("");
            }}
            disabled={account.profile.verification_status !== "verified"}
          >
            <Plus size={18} />
            New listing
          </button>
        )}
      </header>
      <Feedback error={error} success={success} />
      {error && !selected && !application && !editing && (
        <button
          className="secondary"
          onClick={() =>
            initialId || initialApplicationId
              ? setDetailRevision((n) => n + 1)
              : void load()
          }
          disabled={busy}
        >
          Retry loading
        </button>
      )}
      {company && account.profile.verification_status !== "verified" && (
        <div className="verification-banner">
          <p>
            Company verification is required to create or publish opportunities.
            Complete your company profile for administrator review.
          </p>
        </div>
      )}
      {editing ? (
        <section className="panel" key={editing === "new" ? "new" : editing.id}>
          <div className="detail-toolbar">
            <h2>
              {editing === "new" ? "Create an opportunity" : "Edit opportunity"}
            </h2>
            <button className="secondary" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </div>
          <form onSubmit={saveListing}>
            <Input
              name="title"
              label="Opportunity title"
              value={editing === "new" ? "" : editing.title}
              required
            />
            <div className="field">
              <label htmlFor="market-type">Opportunity type</label>
              <select
                id="market-type"
                name="type"
                defaultValue={editing === "new" ? "ojt" : editing.type}
              >
                <option value="ojt">OJT</option>
                <option value="job">Job</option>
              </select>
            </div>
            <Input
              name="location"
              label="Location"
              value={editing === "new" ? "" : editing.location}
              required
            />
            <Input
              name="skills"
              label="Skills (separate with commas)"
              value={editing === "new" ? "" : editing.skills.join(", ")}
              maxLength={2500}
            />
            <Input
              name="description"
              label="Description"
              kind="textarea"
              maxLength={10000}
              value={editing === "new" ? "" : editing.description}
              required
            />
            <Input
              name="requirements"
              label="Requirements"
              kind="textarea"
              maxLength={10000}
              value={editing === "new" ? "" : editing.requirements}
              required
            />
            <button className="primary" disabled={busy}>
              {busy ? "Saving…" : "Save listing"}
            </button>
          </form>
        </section>
      ) : application ? (
        <section className="panel">
          <button
            className="back-button"
            onClick={() => {
              setApplication(null);
              onApplication?.(undefined);
              setSuccess("");
            }}
          >
            <ArrowLeft size={16} />
            Back to {applicationMode ? "applications" : "opportunities"}
          </button>
          <div className="detail-toolbar">
            <div>
              <h2>{application.listing_title}</h2>
              <p className="muted">{application.company_name}</p>
            </div>
            <StatusBadge status={application.status} />
          </div>
          {application.status === "submitted" && mode !== "review" && (
            <p className="application-receipt" role="status">
              Your application is with {application.company_name}. Status
              updates appear on this page.
            </p>
          )}
          <dl className="receipt">
            <dt>Application reference</dt>
            <dd>{application.reference}</dd>
            <dt>Submitted (Asia/Manila)</dt>
            <dd>{manila(application.created_at)}</dd>
            {mode === "review" && (
              <>
                <dt>Applicant</dt>
                <dd>{application.student_name}</dd>
              </>
            )}
          </dl>
          <h3>Cover letter</h3>
          <p className="preserve-lines">
            {application.cover_letter || "No cover letter provided."}
          </p>
          <a
            className="secondary"
            href={`/api/v1/applications/${application.id}/attachment`}
          >
            <Download size={16} />
            Download {application.attachment_name}
          </a>
          {mode === "review" && application.student_profile && (
            <section className="applicant-profile">
              <h3>Applicant background</h3>
              <p>
                {application.student_profile.program} ·{" "}
                {application.student_profile.institution}
              </p>
              <p>{application.student_profile.location}</p>
              <p>{application.student_profile.background}</p>
              <p>
                Skills:{" "}
                {application.student_profile.skills.join(", ") ||
                  "Not provided"}
              </p>
            </section>
          )}
          <h3 className="history-title">Status history</h3>
          <ol className="timeline">
            {application.history.map((h, i) => (
              <li key={i}>
                <strong>{statusLabel(h.new_status)}</strong>
                <time>{manila(h.created_at)}</time>
              </li>
            ))}
          </ol>
          {mode === "review" &&
            ["submitted", "under_review"].includes(application.status) && (
              <form className="decision-form" onSubmit={decide}>
                <div className="field">
                  <label htmlFor="review-status">New application status</label>
                  <select
                    id="review-status"
                    required
                    value={decision}
                    onChange={(e) => setDecision(e.target.value)}
                  >
                    <option value="">Choose a status</option>
                    {application.status === "submitted" ? (
                      <option value="under_review">Under review</option>
                    ) : (
                      <option value="accepted">Accepted</option>
                    )}
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
                <p className="muted">
                  Accepted and rejected decisions are final. This change is
                  visible to the student and retained in history.
                </p>
                <button className="primary" disabled={busy || !decision}>
                  Confirm status change
                </button>
              </form>
            )}
        </section>
      ) : selected ? (
        <section className="panel">
          <button
            className="back-button"
            onClick={() => {
              setSelected(null);
              onListing?.(undefined);
              setSuccess("");
              setError("");
            }}
          >
            <ArrowLeft size={16} />
            Back to opportunities
          </button>
          <div className="detail-toolbar">
            <div>
              <h2>{selected.title}</h2>
              <p className="muted">{selected.company_name}</p>
            </div>
            <StatusBadge status={selected.status} />
          </div>
          <div className="listing-artwork-cover" aria-hidden="true">
            <Artwork kind="opportunities" />
          </div>
          <Tags listing={selected} />
          <h3 className="detail-section">About this opportunity</h3>
          <p className="preserve-lines">{selected.description}</p>
          <h3 className="detail-section">What you’ll need</h3>
          <p className="preserve-lines">{selected.requirements}</p>
          {selected.company_description && (
            <>
              <h3>About {selected.company_name}</h3>
              <p>{selected.company_description}</p>
            </>
          )}
          {selected.company_website && (
            <p>
              <a
                href={selected.company_website}
                target="_blank"
                rel="noreferrer"
              >
                Visit company website
              </a>
            </p>
          )}
          {company ? (
            <div className="listing-actions">
              {selected.status !== "closed" && (
                <button
                  className="secondary"
                  onClick={() => setEditing(selected)}
                >
                  Edit listing
                </button>
              )}
              {selected.status === "draft" && (
                <button
                  className="primary"
                  disabled={busy}
                  onClick={() => setPendingAction("publish")}
                >
                  Publish listing
                </button>
              )}
              {selected.status === "published" && (
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() => setPendingAction("close")}
                >
                  Close listing
                </button>
              )}
              {pendingAction && (
                <div className="confirmation">
                  <h3>
                    {pendingAction === "publish"
                      ? "Publish this opportunity?"
                      : "Close this opportunity?"}
                  </h3>
                  <p>
                    {pendingAction === "publish"
                      ? "Students will be able to find this listing and submit applications."
                      : "New applications will stop. Existing submissions remain available. A closed listing cannot be reopened."}
                  </p>
                  <div className="actions">
                    <button
                      className="secondary"
                      onClick={() => setPendingAction(null)}
                    >
                      Cancel
                    </button>
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={transition}
                    >
                      Confirm {pendingAction}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : account.user.role === "student" ? (
            <>
              <button
                className="primary"
                disabled={selected.status !== "published"}
                onClick={() => setApplying(!applying)}
              >
                {selected.status === "closed"
                  ? "Applications closed"
                  : applying
                    ? "Hide application form"
                    : "Apply to opportunity"}
                <ArrowRight size={17} />
              </button>
              <form
                hidden={!applying}
                className="apply-form"
                onSubmit={submitApplication}
              >
                <div hidden={confirm}>
                  <h3>Your application</h3>
                  <Input
                    name="cover_letter"
                    label="Cover letter (optional)"
                    kind="textarea"
                    maxLength={5000}
                  />
                  <div className="field">
                    <label htmlFor="application-file">
                      Resume or requirement (PDF, up to 5 MiB, required)
                    </label>
                    <input
                      type="file"
                      id="application-file"
                      name="file"
                      accept="application/pdf,.pdf"
                      required
                      onChange={() => setConfirm(false)}
                    />
                  </div>
                  <p className="privacy">
                    Only you and the reviewing company can download this
                    document.
                  </p>
                </div>
                {confirm && (
                  <div className="review-summary">
                    <h3>Review your application</h3>
                    <dl>
                      <dt>Opportunity</dt>
                      <dd>{selected.title}</dd>
                      <dt>Company</dt>
                      <dd>{selected.company_name}</dd>
                      <dt>Attached PDF</dt>
                      <dd>
                        {reviewFile?.name} ·{" "}
                        {Math.ceil((reviewFile?.size || 0) / 1024)} KB
                      </dd>
                    </dl>
                    <h4>Cover letter</h4>
                    <p className="preserve-lines">
                      {reviewLetter || "No cover letter included."}
                    </p>
                    <p className="privacy">
                      Confirming sends your cover letter and PDF to{" "}
                      {selected.company_name}. You can apply only once to this
                      listing.
                    </p>
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => setConfirm(false)}
                    >
                      Edit application
                    </button>
                  </div>
                )}
                <button className="primary" disabled={busy}>
                  {busy
                    ? "Submitting…"
                    : confirm
                      ? "Confirm and submit"
                      : "Review application"}
                </button>
              </form>
            </>
          ) : (
            <p className="muted">Only students can submit applications.</p>
          )}
        </section>
      ) : (
        <>
          {!company && !applicationMode && (
            <form className="search-bar" key={filters} onSubmit={search}>
              <div className="field">
                <label htmlFor="search-q">Keyword</label>
                <input
                  id="search-q"
                  name="q"
                  defaultValue={new URLSearchParams(filters).get("q") || ""}
                  placeholder="Role, title or keyword"
                />
              </div>
              <div className="field">
                <label htmlFor="search-location">Location</label>
                <input
                  id="search-location"
                  name="location"
                  defaultValue={
                    new URLSearchParams(filters).get("location") || ""
                  }
                  placeholder="City or remote"
                />
              </div>
              <div className="field">
                <label htmlFor="search-type">Type</label>
                <select
                  id="search-type"
                  name="type"
                  defaultValue={new URLSearchParams(filters).get("type") || ""}
                >
                  <option value="">All types</option>
                  <option value="ojt">OJT</option>
                  <option value="job">Job</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="search-skill">Skill</label>
                <input
                  id="search-skill"
                  name="skill"
                  defaultValue={new URLSearchParams(filters).get("skill") || ""}
                  placeholder="e.g. Python"
                />
              </div>
              <button className="primary" disabled={busy}>
                <Search size={17} />
                Search
              </button>
              {filters && (
                <button
                  type="button"
                  className="filter-reset"
                  onClick={(e) => {
                    const form = e.currentTarget.form;
                    setFilters("");
                    onFilters?.("");
                    setOffset(0);
                    requestAnimationFrame(() => form?.reset());
                  }}
                >
                  Clear filters
                </button>
              )}
            </form>
          )}
          {mode === "browse" && account.user.role === "student" && (
            <SuggestionsPreview
              kind="listing"
              onOpen={(id) => void open({ id })}
            />
          )}
          <section className="panel">
            <div className="section-title">
              <h2>
                {applicationMode
                  ? "Applications"
                  : company
                    ? "Manage listings"
                    : "Available opportunities"}
              </h2>
              <span>
                {total} {total === 1 ? "result" : "results"}
              </span>
            </div>
            {busy ? (
              <p role="status">
                {applicationMode
                  ? "Loading applications…"
                  : "Loading opportunities…"}
              </p>
            ) : error ? (
              <p className="muted">
                Results could not be loaded. Use Retry loading above to try
                again.
              </p>
            ) : total === 0 ? (
              <div className="empty">
                <BriefcaseBusiness size={32} />
                <h3>
                  {applicationMode
                    ? "No applications yet"
                    : company
                      ? "No listings yet"
                      : "No opportunities found"}
                </h3>
                <p>
                  {applicationMode
                    ? mode === "applications"
                      ? "You haven’t applied yet. Find an open opportunity and check its requirements."
                      : "Applications appear here when students submit to one of your open listings."
                    : company
                      ? "Create a draft when your company is verified."
                      : "Try changing your filters or check again when companies publish listings."}
                </p>
                {mode === "applications" && (
                  <a className="secondary" href={href("opportunities")}>
                    Find opportunities
                    <ArrowRight size={16} />
                  </a>
                )}
              </div>
            ) : applicationMode ? (
              apps.map((a) => (
                <button
                  className="application-row"
                  key={a.id}
                  onClick={() => viewApplication(a)}
                >
                  <div>
                    <h3>{a.listing_title}</h3>
                    <p>{mode === "review" ? a.student_name : a.company_name}</p>
                    <small>
                      {a.reference} · {manila(a.created_at)}
                    </small>
                  </div>
                  <StatusBadge status={a.status} />
                </button>
              ))
            ) : (
              items.map((l) => (
                <article className="listing-row" key={l.id}>
                  <div className="opportunity-emblem" aria-hidden="true">
                    <ThinkIcon name="opportunities" size={40} />
                  </div>
                  <div className="detail-toolbar">
                    <div>
                      <p className="company-name">{l.company_name}</p>
                      <h3>
                        <button onClick={() => open(l)}>{l.title}</button>
                      </h3>
                    </div>
                    {company && <StatusBadge status={l.status} />}
                  </div>
                  <Tags listing={l} />
                  <p className="listing-summary">
                    {l.description.slice(0, 200)}
                    {l.description.length > 200 ? "…" : ""}
                  </p>
                  <button className="text-button" onClick={() => open(l)}>
                    View opportunity <ArrowRight size={15} />
                  </button>
                </article>
              ))
            )}
            <Pager
              total={total}
              offset={offset}
              busy={busy}
              onChange={setOffset}
            />
          </section>
        </>
      )}
    </>
  );
}
