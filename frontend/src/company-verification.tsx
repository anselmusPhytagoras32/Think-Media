// FR11/W08, NFR02/04/05/09: owner-controlled verification with a focused review workspace.
import { useEffect, useRef, useState, type FormEvent } from "react";
import { ArrowLeft, ArrowRight, Check, ExternalLink } from "lucide-react";
import { api, ApiError, type Company } from "./api";
import { CompanyLogo } from "./company-brand";
import { ThinkIcon } from "./brand";
import { WorkspaceArt } from "./workspace-art";
import { StatusBadge } from "./status";
import { useDataRevision } from "./live-data";

type Page = { items: Company[]; total: number };
export function CompanyVerification({
  initialId,
  onCompany,
}: {
  initialId?: string;
  onCompany?: (id?: string) => void;
}) {
  const [items, setItems] = useState<Company[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [status, setStatus] = useState("pending");
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selected, setSelected] = useState<Company | null>(null);
  const [saving, setSaving] = useState(false);
  const [detailBusy, setDetailBusy] = useState(false);
  const [stale, setStale] = useState(false);
  const [decision, setDecision] = useState("");
  const [reason, setReason] = useState("");
  const [fields, setFields] = useState<Record<string, string[]>>({});
  const sequence = useRef(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const opener = useRef<HTMLButtonElement | null>(null);
  const queueHeading = useRef<HTMLHeadingElement>(null);
  const confirmation = useRef<HTMLDivElement>(null);
  const liveRevision = useDataRevision(["accounts"], !saving);
  useEffect(() => {
    if (selected && !detailBusy) heading.current?.focus();
  }, [selected?.id, detailBusy]);
  async function load(background = false) {
    const request = ++sequence.current;
    if (!background) setBusy(true);
    setLoadError("");
    if (!background) { setItems([]); setTotal(null); }
    try {
      const response = await api<Page>(
        `/admin/companies?status=${status}&limit=20&offset=${offset}`,
      );
      if (request === sequence.current) {
        setItems(response.items);
        setTotal(response.total);
      }
    } catch (failure) {
      if (request === sequence.current)
        setLoadError((failure as Error).message);
    } finally {
      if (request === sequence.current) setBusy(false);
    }
  }
  useEffect(() => {
    void load();
    return () => {
      sequence.current++;
    };
  }, [status, offset]);
  useEffect(() => {
    if (liveRevision > 0 && !saving) void load(true);
  }, [liveRevision]);
  useEffect(() => {
    if (!initialId) {
      setSelected(null);
      setDetailBusy(false);
      return;
    }
    let active = true;
    setDetailBusy(true);
    api<Company>(`/admin/companies/${initialId}`)
      .then((company) => {
        if (active) setSelected(company);
      })
      .catch((failure) => {
        if (active) setError(failure.message);
      })
      .finally(() => {
        if (active) setDetailBusy(false);
      });
    return () => {
      active = false;
    };
  }, [initialId]);
  function choose(company: Company, button: HTMLButtonElement) {
    opener.current = button;
    setSelected(company);
    setDecision("");
    setReason("");
    setError("");
    setSuccess("");
    setStale(false);
    setFields({});
    onCompany?.(company.id);
  }
  function closeReview() {
    setSelected(null);
    setError("");
    setStale(false);
    setFields({});
    onCompany?.();
    requestAnimationFrame(() =>
      requestAnimationFrame(() =>
        (opener.current?.isConnected
          ? opener.current
          : queueHeading.current
        )?.focus(),
      ),
    );
  }
  async function review(event: FormEvent) {
    event.preventDefault();
    if (!selected || saving) return;
    setSaving(true);
    setError("");
    setFields({});
    try {
      await api(`/admin/companies/${selected.id}/verification`, "PATCH", {
        status: decision,
        reason,
        expected_version: selected.verification_version,
      });
      setSuccess("Verification decision recorded.");
      setSelected(null);
      setDecision("");
      setReason("");
      onCompany?.();
      await load();
      requestAnimationFrame(() => confirmation.current?.focus());
    } catch (failure) {
      setError((failure as Error).message);
      if (failure instanceof ApiError) {
        setFields(failure.fields);
        setStale(failure.status === 409);
      }
    } finally {
      setSaving(false);
    }
  }
  async function refreshSelected() {
    if (!selected) return;
    setDetailBusy(true);
    setError("");
    try {
      setSelected(await api<Company>(`/admin/companies/${selected.id}`));
      setStale(false);
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setDetailBusy(false);
    }
  }
  return (
    <div
      className={`verification-page ${selected || detailBusy ? "has-selection" : ""}`}
    >
      <header className="verification-page-heading">
        <div>
          <a className="role-back-link" href="#/overview">
            <ArrowLeft size={15} /> Administration
          </a>
          <h1>
            Company <em>verification.</em>
          </h1>
          <p>
            Review the organization. Record the decision. Keep opportunities
            trustworthy.
          </p>
        </div>
        <span className="verification-heading-mark">
          <ThinkIcon name="verification" size={38} />
        </span>
      </header>
      {success && (
        <div
          ref={confirmation}
          tabIndex={-1}
          className="notice success"
          role="status"
        >
          <Check size={18} />
          {success}
        </div>
      )}
      {error && !selected && (
        <div className="notice error" role="alert">
          {error}
        </div>
      )}
      <div className="verification-workspace">
        <section
          className="verification-queue"
          aria-labelledby="verification-queue-title"
        >
          <div className="verification-queue-heading">
            <h2 id="verification-queue-title" ref={queueHeading} tabIndex={-1}>
              Organizations {total !== null && <span>{total}</span>}
            </h2>
            <label htmlFor="verification-filter">
              Verification status
              <select
                id="verification-filter"
                value={status}
                disabled={saving}
                onChange={(event) => {
                  setStatus(event.target.value);
                  setOffset(0);
                  setSelected(null);
                  setError("");
                  setSuccess("");
                  onCompany?.();
                }}
              >
                <option value="pending">Pending</option>
                <option value="verified">Verified</option>
                <option value="rejected">Rejected</option>
              </select>
            </label>
          </div>
          {busy ? (
            <p className="role-loading" role="status">
              Loading organizations…
            </p>
          ) : loadError ? (
            <div className="verification-queue-empty" role="alert">
              <ThinkIcon name="organization" size={34} />
              <h3>Could not load organizations</h3>
              <p>{loadError}</p>
              <button
                type="button"
                className="secondary"
                onClick={() => void load()}
              >
                Retry loading
              </button>
            </div>
          ) : items.length ? (
            <div className="verification-queue-records">
              {items.map((company) => (
                <article
                  key={company.id}
                  className={`verification-company ${selected?.id === company.id ? "is-selected" : ""}`}
                >
                  <CompanyLogo
                    companyId={company.id}
                    companyName={company.company_name}
                  />
                  <div>
                    <h3>{company.company_name}</h3>
                    <p>{company.location || "Location not provided"}</p>
                    <StatusBadge status={company.verification_status} />
                  </div>
                  <button
                    type="button"
                    className="verification-review-button"
                    aria-label="Review"
                    aria-describedby={`company-name-${company.id}`}
                    aria-pressed={selected?.id === company.id}
                    disabled={saving}
                    onClick={(event) => choose(company, event.currentTarget)}
                  >
                    Review <ArrowRight size={15} />
                  </button>
                  <span className="sr-only" id={`company-name-${company.id}`}>
                    {company.company_name}
                  </span>
                </article>
              ))}
            </div>
          ) : (
            <div className="verification-queue-empty">
              <ThinkIcon name="verification" size={36} />
              <h3>No {status} organizations</h3>
              <p>
                {status === "pending"
                  ? "New company registrations will appear here when they need a review."
                  : "Companies with this verification status will appear here."}
              </p>
            </div>
          )}
          {!loadError && total !== null && total > 20 && (
            <nav
              className="verification-pagination"
              aria-label="Company queue pages"
            >
              <button
                type="button"
                className="secondary"
                disabled={offset === 0 || busy || saving}
                onClick={() => {
                  setSelected(null);
                  setOffset(offset - 20);
                }}
              >
                Previous
              </button>
              <span>
                {offset + 1}–{Math.min(offset + 20, total)} of {total}
              </span>
              <button
                type="button"
                className="secondary"
                disabled={offset + 20 >= total || busy || saving}
                onClick={() => {
                  setSelected(null);
                  setOffset(offset + 20);
                }}
              >
                Next
              </button>
            </nav>
          )}
        </section>
        <section className="verification-detail" aria-label="Company review">
          {detailBusy ? (
            <p className="role-loading" role="status">
              Loading company details…
            </p>
          ) : selected ? (
            <>
              <button
                type="button"
                className="role-back-link verification-back"
                onClick={closeReview}
                disabled={saving}
              >
                <ArrowLeft size={16} /> Back to queue
              </button>
              <div className="verification-company-heading">
                <CompanyLogo
                  companyId={selected.id}
                  companyName={selected.company_name}
                />
                <div>
                  <h2 ref={heading} tabIndex={-1}>
                    Review {selected.company_name}
                  </h2>
                  <StatusBadge status={selected.verification_status} />
                </div>
              </div>
              <div className="verification-company-about">
                <h3>About the organization</h3>
                <p className="preserve-lines">
                  {selected.description || "No company description supplied."}
                </p>
              </div>
              <dl className="verification-company-facts">
                <div>
                  <dt>Location</dt>
                  <dd>{selected.location || "Not supplied"}</dd>
                </div>
                <div>
                  <dt>Contact email</dt>
                  <dd>{selected.contact_email || "Not supplied"}</dd>
                </div>
                <div>
                  <dt>Contact phone</dt>
                  <dd>{selected.contact_phone || "Not supplied"}</dd>
                </div>
                <div>
                  <dt>Website</dt>
                  <dd>
                    {selected.website ? (
                      <a
                        href={selected.website}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Company website <ExternalLink size={13} />
                        <span className="sr-only"> (opens in a new tab)</span>
                      </a>
                    ) : (
                      "Not supplied"
                    )}
                  </dd>
                </div>
              </dl>
              {selected.verification_status === "pending" ? (
                <form className="verification-decision-form" onSubmit={review}>
                  <div className="verification-form-heading">
                    <ThinkIcon name="verification" size={24} />
                    <div>
                      <h3>Record your decision</h3>
                      <p>
                        Check the organization details against your verification
                        evidence.
                      </p>
                    </div>
                  </div>
                  {error && (
                    <div className="notice error" role="alert">
                      {error}
                      {stale && (
                        <button
                          type="button"
                          className="text-button"
                          onClick={() => void refreshSelected()}
                        >
                          Refresh company details
                        </button>
                      )}
                    </div>
                  )}
                  <label htmlFor="verification-decision">Decision</label>
                  <select
                    id="verification-decision"
                    required
                    value={decision}
                    disabled={saving}
                    aria-invalid={!!fields.status}
                    aria-describedby="verification-decision-hint"
                    onChange={(event) => setDecision(event.target.value)}
                  >
                    <option value="" disabled>
                      Choose a decision
                    </option>
                    <option value="verified">Verify company</option>
                    <option value="rejected">Reject verification</option>
                  </select>
                  <p
                    className="verification-field-hint"
                    id="verification-decision-hint"
                  >
                    {fields.status?.join(" ") ||
                      (decision === "verified"
                        ? "Verification allows this company to create and publish listings."
                        : decision === "rejected"
                          ? "This company will remain unable to create or publish listings."
                          : "Verification enables publishing. Rejection keeps publishing disabled.")}
                  </p>
                  <label htmlFor="verification-reason">
                    Reason for decision
                  </label>
                  <textarea
                    id="verification-reason"
                    required
                    rows={3}
                    maxLength={1000}
                    value={reason}
                    disabled={saving}
                    aria-invalid={!!fields.reason}
                    aria-describedby="verification-reason-hint"
                    onChange={(event) => setReason(event.target.value)}
                  />
                  <p
                    className="verification-field-hint"
                    id="verification-reason-hint"
                  >
                    {fields.reason?.join(" ") ||
                      "Include the evidence you checked. Your reason is saved in the audit history."}
                  </p>
                  <div className="verification-decision-actions">
                    <button
                      className="secondary"
                      type="button"
                      disabled={saving}
                      onClick={closeReview}
                    >
                      Cancel
                    </button>
                    <button className="primary" disabled={saving || stale}>
                      {saving ? "Recording decision…" : "Confirm decision"}
                      <ArrowRight size={16} />
                    </button>
                  </div>
                </form>
              ) : (
                <div className="verification-recorded">
                  <ThinkIcon name="audit" size={23} />
                  <p>
                    {selected.verification_status === "verified"
                      ? "This company is verified and can publish its opportunities."
                      : "This company is not verified. Publishing remains disabled."}
                  </p>
                  <a href="#/audit">
                    Open audit history <ArrowRight size={14} />
                  </a>
                </div>
              )}
            </>
          ) : (
            <div className="verification-start">
              <WorkspaceArt kind="verification" />
              <h2>
                {!busy && !loadError && total === 0
                  ? "You’re up to date."
                  : "A good opportunity starts with a trusted company."}
              </h2>
              <p>
                {!busy && !loadError && total === 0
                  ? "There are no organizations in this queue. Change the status to view past decisions."
                  : "Choose an organization from the queue to see its details and record a verification decision."}
              </p>
              <div className="verification-review-points">
                <span>
                  <ThinkIcon name="organization" size={20} /> Organization
                  details
                </span>
                <span>
                  <ThinkIcon name="profile" size={20} /> Contact information
                </span>
                <span>
                  <ThinkIcon name="audit" size={20} /> A recorded reason
                </span>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
