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
  ShieldCheck,
  SlidersHorizontal,
  UserRound,
} from "lucide-react";
import { api, Account, manila } from "./api";
import { SuggestionsPreview } from "./suggestions-preview";
import { StatusBadge } from "./status";
import { ThinkIcon } from "./brand";
import { Artwork } from "./artwork";
import { href } from "./navigation";
import { CompanyLogo, CompanyCover } from "./company-brand";
import { useDataRevision } from "./live-data";
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
  attachment_available?: boolean;
  attachment_deleted_at?: string | null;
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
// FR05/07; NFR03/05/09/11: downloads stay private and expiry preserves context.
function ApplicationAttachment({ application }: { application: Application }) {
  const [busy, setBusy] = useState(false);
  const [expiredDuringDownload, setExpiredDuringDownload] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const mounted = useRef(false);
  const controller = useRef<AbortController | null>(null);
  const urls = useRef(new Set<string>());
  const releaseTimers = useRef(new Set<number>());
  const expiredHeading = useRef<HTMLHeadingElement>(null);
  const expired =
    application.attachment_available === false || expiredDuringDownload;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      controller.current?.abort();
      releaseTimers.current.forEach((timer) => window.clearTimeout(timer));
      urls.current.forEach((url) => URL.revokeObjectURL(url));
      releaseTimers.current.clear();
      urls.current.clear();
    };
  }, []);
  useEffect(() => {
    if (expiredDuringDownload) expiredHeading.current?.focus();
  }, [expiredDuringDownload]);
  async function download() {
    if (busy || expired) return;
    setBusy(true);
    setError("");
    setStatus("");
    const request = new AbortController();
    controller.current = request;
    const timeout = window.setTimeout(() => request.abort(), 30000);
    const limit = 5 * 1024 * 1024;
    try {
      const response = await fetch(
        `/api/v1/applications/${application.id}/attachment`,
        {
          credentials: "same-origin",
          cache: "no-store",
          signal: request.signal,
        },
      );
      if (response.status === 410) {
        await response.body?.cancel();
        if (mounted.current) setExpiredDuringDownload(true);
        return;
      }
      if (!response.ok) {
        const failure = await response.json().catch(() => null);
        throw new Error(
          typeof failure?.error?.message === "string"
            ? failure.error.message.slice(0, 1000)
            : "The attachment could not be downloaded. Try again.",
        );
      }
      if (Number(response.headers.get("content-length")) > limit) {
        await response.body?.cancel();
        throw new Error(
          "This download exceeds the supported 5 MiB limit. Try again later.",
        );
      }
      if (
        response.headers
          .get("content-type")
          ?.split(";")[0]
          .trim()
          .toLowerCase() !== "application/pdf" ||
        !response.body
      ) {
        await response.body?.cancel();
        throw new Error("The attachment was not returned as a PDF. Try again.");
      }
      const reader = response.body.getReader();
      const chunks: Uint8Array<ArrayBuffer>[] = [];
      let size = 0;
      try {
        while (true) {
          const next = await reader.read();
          if (next.done) break;
          size += next.value.byteLength;
          if (size > limit) {
            await reader.cancel();
            throw new Error(
              "This download exceeds the supported 5 MiB limit. Try again later.",
            );
          }
          chunks.push(new Uint8Array(next.value));
        }
      } finally {
        reader.releaseLock();
      }
      if (!size) throw new Error("The attachment was empty. Try again.");
      if (!mounted.current) return;
      const url = URL.createObjectURL(
        new Blob(chunks, { type: "application/pdf" }),
      );
      urls.current.add(url);
      const link = document.createElement("a");
      link.href = url;
      link.download = application.attachment_name;
      link.hidden = true;
      document.body.append(link);
      link.click();
      link.remove();
      // Allow the browser to dispatch the download, then release the private blob.
      const release = window.setTimeout(() => {
        URL.revokeObjectURL(url);
        urls.current.delete(url);
        releaseTimers.current.delete(release);
      }, 1000);
      releaseTimers.current.add(release);
      setStatus("Download started. Keep this PDF private.");
    } catch (failure) {
      if (mounted.current)
        setError(
          request.signal.aborted
            ? "The download took too long. Try again."
            : failure instanceof Error
              ? failure.message
              : "The attachment could not be downloaded. Try again.",
        );
    } finally {
      window.clearTimeout(timeout);
      if (controller.current === request) controller.current = null;
      if (mounted.current) setBusy(false);
    }
  }
  if (expired)
    return (
      <section
        className="notice"
        aria-labelledby={`expired-attachment-${application.id}`}
      >
        <div>
          <h3
            id={`expired-attachment-${application.id}`}
            ref={expiredHeading}
            tabIndex={-1}
          >
            Attachment expired
          </h3>
          <p>
            This file is no longer available under the retention policy. The
            application reference and status history remain available.
          </p>
          {application.attachment_deleted_at && (
            <p>
              Expired (Asia/Manila):{" "}
              <time dateTime={application.attachment_deleted_at}>
                {manila(application.attachment_deleted_at)}
              </time>
            </p>
          )}
        </div>
      </section>
    );
  return (
    <>
      <button
        className="secondary"
        disabled={busy}
        onClick={() => void download()}
      >
        <Download size={16} />
        {busy
          ? "Downloading attachment…"
          : `Download ${application.attachment_name}`}
      </button>
      <p role="status" aria-live="polite">
        {busy ? "Downloading the private PDF…" : status}
      </p>
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
    </>
  );
}
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
// FR02/04/05/08; NFR05/09: search-first discovery with real filters and a separate suggestion view.
function OpportunityBrowse({
  account,
  items,
  total,
  busy,
  error,
  filters,
  offset,
  onSearch,
  onReset,
  onOpen,
  onPage,
  view,
  onView,
}: {
  account: Account;
  items: Listing[];
  total: number;
  busy: boolean;
  error: string;
  filters: string;
  offset: number;
  onSearch: (event: FormEvent<HTMLFormElement>) => void;
  onReset: () => void;
  onOpen: (listing: Pick<Listing, "id">) => void;
  onPage: (offset: number) => void;
  view: "all" | "suggested";
  onView: (view: "all" | "suggested") => void;
}) {
  const params = new URLSearchParams(filters);
  const student = account.user.role === "student";
  const [filtersOpen, setFiltersOpen] = useState(
    () => window.matchMedia("(min-width:980px)").matches,
  );
  useEffect(() => {
    const media = window.matchMedia("(min-width:980px)");
    const update = () => setFiltersOpen(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  return (
    <div className="opportunity-browser">
      <form
        id="opportunity-search"
        className="opportunity-search"
        onSubmit={(event) => {
          onView("all");
          onSearch(event);
        }}
        role="search"
        aria-label="Find opportunities"
      >
        <div className="opportunity-keyword field">
          <label htmlFor="search-q">Keyword</label>
          <div className="opportunity-search-input">
            <Search size={20} aria-hidden="true" />
            <input
              id="search-q"
              name="q"
              defaultValue={params.get("q") || ""}
              placeholder="Search by role, title or keyword"
            />
          </div>
        </div>
        <button className="primary" disabled={busy}>
          <Search size={17} />
          Search
        </button>
      </form>
      <div className={`opportunity-grid ${student ? "has-support" : ""}`}>
        <aside className="opportunity-filters" aria-label="Opportunity filters">
          <button
            type="button"
            className="opportunity-filter-toggle"
            aria-expanded={filtersOpen}
            aria-controls="opportunity-filter-fields"
            onClick={() => setFiltersOpen(!filtersOpen)}
          >
            <SlidersHorizontal size={18} /> Filters{" "}
            <span>{filtersOpen ? "Hide" : "Show"}</span>
          </button>
          <div
            className="opportunity-filter-fields"
            id="opportunity-filter-fields"
            hidden={!filtersOpen}
          >
            <h2>Filter opportunities</h2>
            <div className="field">
              <label htmlFor="search-type">Type</label>
              <select
                id="search-type"
                name="type"
                form="opportunity-search"
                defaultValue={params.get("type") || ""}
              >
                <option value="">All types</option>
                <option value="ojt">OJT</option>
                <option value="job">Job</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="search-location">Location</label>
              <input
                id="search-location"
                name="location"
                form="opportunity-search"
                defaultValue={params.get("location") || ""}
                placeholder="City or remote"
              />
            </div>
            <div className="field">
              <label htmlFor="search-skill">Skill</label>
              <input
                id="search-skill"
                name="skill"
                form="opportunity-search"
                defaultValue={params.get("skill") || ""}
                placeholder="e.g. Python"
              />
            </div>
            <button
              className="secondary"
              form="opportunity-search"
              disabled={busy}
            >
              Apply filters
            </button>
            <p className="opportunity-filter-note">
              <ShieldCheck size={16} />
              Published listings from verified companies.
            </p>
          </div>
        </aside>
        <section
          className="opportunity-results"
          aria-label="Opportunity results"
          aria-busy={busy}
        >
          <div
            className="opportunity-views"
            role="group"
            aria-label="Opportunity views"
          >
            <button
              type="button"
              aria-pressed={view === "all"}
              onClick={() => onView("all")}
            >
              All opportunities
            </button>
            {student && (
              <button
                type="button"
                aria-pressed={view === "suggested"}
                onClick={() => onView("suggested")}
              >
                For you
              </button>
            )}
          </div>
          {view === "suggested" ? (
            <div className="opportunity-personalized">
              <p>
                Explore suggestions based on your profile and activity.{" "}
                <a href={href("profile")}>Update your profile</a>
              </p>
              <SuggestionsPreview
                kind="listing"
                browseHint="Choose Browse all opportunities below to continue searching, or update your profile."
                onOpen={(id) => onOpen({ id })}
              />
              <button
                type="button"
                className="secondary"
                onClick={() => onView("all")}
              >
                Browse all opportunities
              </button>
            </div>
          ) : (
            <>
              <div className="opportunity-results-heading">
                <h2>Available opportunities</h2>
                <span role="status">
                  {busy
                    ? "Searching…"
                    : `${total} ${total === 1 ? "result" : "results"}`}
                </span>
                {filters && (
                  <button
                    type="button"
                    className="text-button"
                    onClick={onReset}
                  >
                    Clear filters
                  </button>
                )}
              </div>
              {filters && (
                <p className="opportunity-active-filters">
                  {[
                    params.get("q") && `Keyword: ${params.get("q")}`,
                    params.get("type") &&
                      `Type: ${params.get("type") === "ojt" ? "OJT" : "Job"}`,
                    params.get("location") &&
                      `Location: ${params.get("location")}`,
                    params.get("skill") && `Skill: ${params.get("skill")}`,
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              )}
              {busy ? (
                <p className="opportunity-result-state" role="status">
                  Loading opportunities…
                </p>
              ) : error ? (
                <p className="opportunity-result-state">
                  Results could not be loaded. Use Retry loading above to try
                  again.
                </p>
              ) : total === 0 ? (
                <div className="empty opportunity-result-state">
                  <Search size={30} />
                  <h3>No opportunities found</h3>
                  <p>Try a broader keyword or adjust your filters.</p>
                  {filters && (
                    <button
                      type="button"
                      className="secondary"
                      onClick={onReset}
                    >
                      Reset search
                    </button>
                  )}
                </div>
              ) : (
                items.map((listing) => (
                  <article
                    className="listing-row opportunity-result"
                    key={listing.id}
                  >
                    <div className="opportunity-company">
                      <CompanyLogo
                        companyId={listing.company_id}
                        companyName={listing.company_name}
                      />
                      <div>
                        <p className="company-name">{listing.company_name}</p>
                        <span className="opportunity-verification">
                          <ShieldCheck size={13} />
                          Verified company
                        </span>
                      </div>
                    </div>
                    <h3>
                      <button type="button" onClick={() => onOpen(listing)}>
                        {listing.title}
                      </button>
                    </h3>
                    <div className="opportunity-facts">
                      <span>
                        <BriefcaseBusiness size={15} />
                        {listing.type === "ojt"
                          ? "OJT placement"
                          : "Job opportunity"}
                      </span>
                      <span>
                        <MapPin size={15} />
                        {listing.location}
                      </span>
                    </div>
                    <p className="listing-summary">
                      {listing.description.slice(0, 240)}
                      {listing.description.length > 240 ? "…" : ""}
                    </p>
                    {!!listing.skills.length && (
                      <ul
                        className="opportunity-skills"
                        aria-label="Required skills"
                      >
                        {listing.skills.slice(0, 6).map((skill) => (
                          <li key={skill}>{skill}</li>
                        ))}
                        {listing.skills.length > 6 && (
                          <li>+{listing.skills.length - 6} more</li>
                        )}
                      </ul>
                    )}
                    <div className="opportunity-result-footer">
                      <button
                        type="button"
                        className="text-button"
                        onClick={() => onOpen(listing)}
                      >
                        View opportunity <ArrowRight size={16} />
                      </button>
                      {Number.isFinite(Date.parse(listing.created_at)) && (
                        <time
                          dateTime={listing.created_at}
                          title={manila(listing.created_at)}
                        >
                          Added{" "}
                          {new Intl.DateTimeFormat("en-PH", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                            timeZone: "Asia/Manila",
                          }).format(new Date(listing.created_at))}
                        </time>
                      )}
                    </div>
                  </article>
                ))
              )}
              <Pager
                total={total}
                offset={offset}
                busy={busy}
                onChange={onPage}
              />
            </>
          )}
        </section>
        {student && (
          <aside
            className="opportunity-support"
            aria-label="Application preparation"
          >
            <div className="opportunity-profile-icon">
              <UserRound size={22} />
            </div>
            <h2>Get application-ready</h2>
            <p>Give companies a clear picture of your skills and goals.</p>
            <ol>
              <li>
                <strong>Your profile</strong>
                <span>
                  {account.profile.program && account.profile.skills?.length
                    ? "Your course and skills are included. Keep them up to date."
                    : "Add your course and skills so suggestions reflect your interests."}
                </span>
                <a href={href("profile")}>
                  Review profile <ArrowRight size={14} />
                </a>
              </li>
              <li>
                <strong>Your resume</strong>
                <span>
                  Prepare a PDF up to 5 MiB. You can review it before
                  submitting.
                </span>
              </li>
              <li>
                <strong>Your progress</strong>
                <span>Keep each application and its status in one place.</span>
                <a href={href("applications")}>
                  My applications <ArrowRight size={14} />
                </a>
              </li>
            </ol>
          </aside>
        )}
      </div>
    </div>
  );
}
export function Marketplace({
  account,
  mode,
  initialId,
  initialCreate = false,
  initialApplicationId,
  initialFilters = "",
  onFilters,
  onListing,
  onApplication,
}: {
  account: Account;
  initialId?: string;
  initialCreate?: boolean;
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
  const [confirmDecision, setConfirmDecision] = useState(false);
  const [browseView, setBrowseView] = useState<"all" | "suggested">("all");
  const [reviewFile, setReviewFile] = useState<File | null>(null),
    [reviewLetter, setReviewLetter] = useState("");
  const loadSequence = useRef(0);
  const editorHeading = useRef<HTMLHeadingElement>(null);
  const applicationHeading = useRef<HTMLHeadingElement>(null);
  const decisionHeading = useRef<HTMLHeadingElement>(null);
  const listingConfirmationHeading = useRef<HTMLHeadingElement>(null);
  const liveRevision = useDataRevision(["marketplace", "accounts"], !editing && !applying && !confirm && !confirmDecision && !pendingAction && !decision);
  useEffect(() => { if (editing) editorHeading.current?.focus(); }, [editing]);
  useEffect(() => { if (application && mode === "review") applicationHeading.current?.focus(); }, [application?.id, mode]);
  useEffect(() => { if (confirmDecision) decisionHeading.current?.focus(); }, [confirmDecision]);
  useEffect(() => { if (pendingAction) listingConfirmationHeading.current?.focus(); }, [pendingAction]);
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
  async function load(background = false) {
    const sequence = ++loadSequence.current;
    if (!background) setBusy(true);
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
    if (company && initialCreate && !initialId && account.profile.verification_status === "verified") {
      setSelected(null);
      setEditing("new");
    }
  }, [mode, initialCreate, initialId, account.profile.verification_status]);
  useEffect(() => {
    setApplication(null);
    setDecision("");
    setConfirmDecision(false);
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
  useEffect(() => {
    if (!liveRevision) return;
    let active = true;
    void load(true);
    if (application) {
      api<Application>(`/applications/${application.id}`).then((fresh) => { if (active) setApplication(fresh); }).catch((failure) => { if (active) setError(failure.message); });
    } else if (selected) {
      api<Listing>(`/listings/${selected.id}`).then((fresh) => { if (active) setSelected(fresh); }).catch((failure) => { if (active) { setSelected(null); setError(failure.message); } });
    }
    return () => { active = false; };
  }, [liveRevision]);
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
      setConfirmDecision(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function decide() {
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
      setConfirmDecision(false);
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
      <header
        className={`page-heading ${mode === "browse" ? "opportunity-heading" : ""} ${company || mode === "review" ? "role-page-heading" : ""}`}
      >
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
        {company && !editing && (
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
          <a className="secondary" href={href("profile")}>Open company profile</a>
        </div>
      )}
      {editing ? (
        <section className="panel" key={editing === "new" ? "new" : editing.id}>
          <div className="detail-toolbar">
            <h2 ref={editorHeading} tabIndex={-1}>
              {editing === "new" ? "Create an opportunity" : "Edit opportunity"}
            </h2>
            <button className="secondary" onClick={() => { setEditing(null); if (initialCreate) onListing?.(); }}>
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
              <h2 ref={applicationHeading} tabIndex={-1}>{application.listing_title}</h2>
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
          <ApplicationAttachment
            key={application.id}
            application={application}
          />
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
              <form className="decision-form" onSubmit={(event) => { event.preventDefault(); setConfirmDecision(true); }}>
                <div className="field">
                  <label htmlFor="review-status">New application status</label>
                  <select
                    id="review-status"
                    required
                    value={decision}
                    onChange={(e) => { setDecision(e.target.value); setConfirmDecision(false); }}
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
                {confirmDecision ? (
                  <section className="confirmation" aria-labelledby="decision-review-title">
                    <h3 id="decision-review-title" ref={decisionHeading} tabIndex={-1}>Review status change</h3>
                    <p>Change {application.student_name}'s application from <strong>{statusLabel(application.status)}</strong> to <strong>{statusLabel(decision)}</strong>?</p>
                    <div className="actions">
                      <button type="button" className="secondary" disabled={busy} onClick={() => { setConfirmDecision(false); document.getElementById("review-status")?.focus(); }}>Change selection</button>
                      <button type="button" className="primary" disabled={busy} onClick={() => void decide()}>Confirm status change</button>
                    </div>
                  </section>
                ) : <button className="primary" disabled={busy || !decision}>Review status change</button>}
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
          <div className="company-detail-cover">
            <CompanyCover
              companyId={selected.company_id}
              companyName={selected.company_name}
            />
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
                  id="listing-publish"
                  disabled={busy}
                  onClick={() => setPendingAction("publish")}
                >
                  Publish listing
                </button>
              )}
              {selected.status === "published" && (
                <button
                  className="secondary"
                  id="listing-close"
                  disabled={busy}
                  onClick={() => setPendingAction("close")}
                >
                  Close listing
                </button>
              )}
              {pendingAction && (
                <div className="confirmation">
                  <h3 ref={listingConfirmationHeading} tabIndex={-1}>
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
                      onClick={() => { const action = pendingAction; setPendingAction(null); document.getElementById(`listing-${action}`)?.focus(); }}
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
      ) : mode === "browse" ? (
        <OpportunityBrowse
          view={browseView}
          onView={setBrowseView}
          key={filters}
          account={account}
          items={items}
          total={total}
          busy={busy}
          error={error}
          filters={filters}
          offset={offset}
          onSearch={search}
          onReset={() => {
            setFilters("");
            onFilters?.("");
            setOffset(0);
          }}
          onOpen={(listing) => void open(listing)}
          onPage={setOffset}
        />
      ) : (
        <>
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
                  {mode === "review" && <span className="application-row-action">Review application <ArrowRight size={15} aria-hidden="true" /></span>}
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
