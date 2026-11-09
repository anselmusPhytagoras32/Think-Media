import React, { useEffect, useState, useRef } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  ClipboardList,
  Eye,
  EyeOff,
  BookOpen,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  FileText,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Pin,
  PinOff,
  ShieldCheck,
  Sparkles,
  UserRound,
  X,
} from "lucide-react";
import { api, ApiError, Account, Company, manila } from "./api";
import "@fontsource-variable/manrope";
import "@fontsource-variable/dm-sans";
import { Marketplace } from "./marketplace";
import { Learning, Assistant } from "./learning";
import { Recommendations } from "./recommendations";
import { Operations } from "./operations";
import { Home } from "./home";
import { CompanyLogo } from "./company-brand";
import { BrandMark, ThinkIcon, type IconName } from "./brand";
import { Onboarding } from "./onboarding";
import { hasSeenWelcome, markWelcomeSeen } from "./welcome-state";
import { href, useRoute } from "./navigation";
import "./style.css";
import "./illustrated.css";
import "./discovery.css";
import "./layout.css";
import "./signin.css";
import "./workspace-shell.css";
import "./opportunities.css";
import "./learning-library.css";
import "./content-identity.css";
import "./suggestions.css";
import "./guidance-bubble.css";
import "./role-workspace.css";
import {
  readSidebarPreference,
  saveSidebarPreference,
} from "./navigation-preferences";

function Field({
  label,
  name,
  defaultValue,
  type = "text",
  required = false,
  hint,
  errors,
  children,
  newPassword = false,
}: {
  label: string;
  name: string;
  defaultValue?: string;
  type?: string;
  required?: boolean;
  hint?: string;
  errors?: Record<string, string[]>;
  children?: React.ReactNode;
  newPassword?: boolean;
}) {
  const [visible, setVisible] = useState(false);
  const input = (
    <input
      id={name}
      name={name}
      defaultValue={defaultValue}
      type={type === "password" && visible ? "text" : type}
      required={required}
      maxLength={
        type === "password"
          ? 128
          : name === "display_name"
            ? 100
            : type === "email"
              ? 254
              : type === "url"
                ? 2048
                : ["skills", "interests"].includes(name)
                  ? 2500
                  : name === "reason"
                    ? 1000
                    : 200
      }
      minLength={type === "password" && newPassword ? 12 : undefined}
      autoComplete={
        type === "password"
          ? newPassword
            ? "new-password"
            : "current-password"
          : name === "email"
            ? "email"
            : name === "display_name"
              ? "name"
              : undefined
      }
      aria-invalid={!!errors?.[name]}
      aria-describedby={`${name}-hint`}
    />
  );
  return (
    <div className="field">
      <label htmlFor={name}>
        {label}
        {required && <span aria-hidden="true"> *</span>}
      </label>
      {(React.isValidElement<Record<string, unknown>>(children)
        ? React.cloneElement(children, {
            "aria-invalid": !!errors?.[name],
            "aria-describedby": [
              children.props["aria-describedby"],
              `${name}-hint`,
            ]
              .filter(Boolean)
              .join(" "),
          })
        : children) ||
        (type === "password" ? (
          <div className="password-control">
            {input}
            <button
              type="button"
              aria-label={visible ? "Hide password" : "Show password"}
              onClick={() => setVisible(!visible)}
            >
              {visible ? <EyeOff size={19} /> : <Eye size={19} />}
            </button>
          </div>
        ) : (
          input
        ))}
      <small
        id={`${name}-hint`}
        className={errors?.[name] ? "field-error" : ""}
      >
        {errors?.[name]?.join(" ") || hint}
      </small>
    </div>
  );
}
function Notice({ error, success }: { error?: string; success?: string }) {
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
// W01 / NFR03: presentation policy approved for fictional local data only.
function LocalDemoNotice() {
  return (
    <details className="privacy-disclosure">
      <summary>Local presentation: how demo data is used</summary>
      <p>
        Use fictional account details and sample PDFs only. Account details,
        activity, ratings and applications are kept in the local demo database.
        Your profile and activity help suggestions; ratings are optional.
        Application documents are private to your account and the reviewing demo
        company.
      </p>
      <p>
        The developers and presenters manage this local demonstration. If a
        presenter enables external AI, your question and approved resource
        excerpts are sent to the configured provider. Keep personal details and
        private application information out of questions. This demonstration is
        not ready to collect real personal data.
      </p>
    </details>
  );
}
function Auth({
  onLogin,
  initialMode = "signin",
  onReplay,
}: {
  onLogin: (a: Account) => void;
  initialMode?: "signup" | "signin";
  onReplay: () => void;
}) {
  const [register, setRegister] = useState(initialMode === "signup"),
    [role, setRole] = useState("student"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [fields, setFields] = useState<Record<string, string[]>>({});
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setFields({});
    const data = Object.fromEntries(new FormData(e.currentTarget));
    let accountCreated = false;
    try {
      if (register) {
        await api("/auth/register", "POST", { ...data, role });
        accountCreated = true;
      }
      onLogin(
        await api<Account>("/auth/login", "POST", {
          email: data.email,
          password: data.password,
        }),
      );
    } catch (err) {
      if (accountCreated) {
        setRegister(false);
        setError(
          "Your account was created. Sign in to continue. " +
            (err as Error).message,
        );
      } else setError((err as Error).message);
      if (err instanceof ApiError) setFields(err.fields);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-layout illustrated-signin">
      <section className="auth-story">
        <a className="brand" href="#">
          <BrandMark />
          <span>
            ThinkMedia<span className="brand-dot">.</span>
          </span>
        </a>
        <picture className="auth-illustration">
          <img
            className="signin-scene"
            src="/illustrations/thinkmedia-signin-flat.png"
            width="1586"
            height="992"
            alt=""
            fetchPriority="high"
            decoding="async"
          />
        </picture>
        <div className="auth-story-copy">
          <h2>
            Learn, find OJT,
            <br />
            and track your applications.
          </h2>
          <p>
            Career preparation, verified company listings and your application
            history in one place.
          </p>
          <div className="story-steps">
            <span>
              <BookOpen />
              Learn workplace skills
            </span>
            <span>
              <BriefcaseBusiness />
              Explore OJT opportunities
            </span>
            <span>
              <FileText />
              Track each application
            </span>
          </div>
        </div>
        <p className="story-footer">
          For students, instructors and participating companies.
        </p>
      </section>
      <main className="auth-main">
        <div className={register ? "auth-box is-register" : "auth-box"}>
          <a className="auth-form-brand brand" href="#">
            <BrandMark size={32} />
            <span>
              ThinkMedia<span className="brand-dot">.</span>
            </span>
          </a>
          <div className="tabs">
            <button
              aria-pressed={!register}
              onClick={() => {
                setRegister(false);
                setError("");
              }}
            >
              Sign in
            </button>
            <button
              aria-pressed={register}
              onClick={() => {
                setRegister(true);
                setError("");
              }}
            >
              Create account
            </button>
          </div>
          <h1 className="auth-title">
            {register ? "Create your account" : "Login to your account"}
          </h1>
          <p className="muted">
            {register
              ? "Choose your role and enter your details."
              : "Continue to your learning, listings and applications."}
          </p>
          <Notice error={error} />
          <form onSubmit={submit}>
            {register && (
              <>
                <Field label="I’m joining as" name="role">
                  <select
                    id="role"
                    aria-describedby="role-note"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                  >
                    <option value="student">Student</option>
                    <option value="instructor">Instructor</option>
                    <option value="company">Company</option>
                  </select>
                </Field>
                <p className="role-note" id="role-note">
                  {role === "student"
                    ? "Find OJT, learn workplace skills and submit applications."
                    : role === "company"
                      ? "Publish listings after verification and review your applicants."
                      : "Browse resources and opportunities to guide your students."}
                </p>
                <Field
                  label="Full name"
                  name="display_name"
                  required
                  errors={fields}
                />
                {role === "company" && (
                  <Field
                    label="Company name"
                    name="company_name"
                    required
                    errors={fields}
                  />
                )}
              </>
            )}
            <Field
              label="Email address"
              name="email"
              type="email"
              required
              errors={fields}
            />
            <Field
              label="Password"
              name="password"
              type="password"
              newPassword={register}
              required
              errors={fields}
              hint={
                register
                  ? "Use 12–128 characters. Your password is never shared."
                  : undefined
              }
            />
            {register && <LocalDemoNotice />}
            <button className="primary wide" disabled={busy}>
              {busy ? "Please wait…" : register ? "Create account" : "Sign in"}
              <ArrowRight size={18} />
            </button>
          </form>
          <p className="auth-help">
            {register ? "Already have an account?" : "New to ThinkMedia?"}{" "}
            <button
              className="text-button"
              onClick={() => setRegister(!register)}
            >
              {register ? "Sign in" : "Create an account"}
            </button>
          </p>
        </div>
        <button className="intro-replay" onClick={onReplay}>
          <ThinkIcon name="guidance" size={19} />
          Getting started
        </button>
        <small className="auth-foot">
          ThinkMedia · OJT preparation & career development
        </small>
      </main>
    </div>
  );
}
function Profile({
  account,
  onSave,
}: {
  account: Account;
  onSave: (a: Account) => void;
}) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [success, setSuccess] = useState(""),
    [errors, setErrors] = useState<Record<string, string[]>>({});
  const p = account.profile;
  async function save(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setSuccess("");
    setErrors({});
    const data: Record<string, unknown> = Object.fromEntries(
      new FormData(e.currentTarget),
    );
    for (const key of ["skills", "interests"])
      if (key in data)
        data[key] = String(data[key])
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
    for (const key of ["website", "contact_email", "contact_phone"])
      if (key in data && !data[key]) data[key] = null;
    try {
      onSave(await api<Account>("/profiles/me", "PATCH", data));
      setSuccess("Your profile has been saved.");
    } catch (err) {
      setError((err as Error).message);
      if (err instanceof ApiError) setErrors(err.fields);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <header className={`page-heading ${p.kind === "company" || p.kind === "administrator" ? "role-page-heading" : ""}`}>
        <div>
          <h1>Your profile</h1>
          <p>{p.kind === "company" ? "Update the organization details used for verification and listings." : "Update the details used in your account."}</p>
        </div>
        <span className="badge">{account.user.role}</span>
      </header>
      <div className="profile-grid">
        <section className="panel">
          <h2>{p.kind === "company" ? "Account and company details" : "Personal information"}</h2>
          <p className="muted">Keep your details up to date.</p>
          <Notice error={error} success={success} />
          {success && p.kind === "student" && (
            <a
              className="profile-next-step secondary"
              href={href("opportunities")}
            >
              Continue to opportunities <ArrowRight size={16} />
            </a>
          )}
          <form onSubmit={save}>
            <Field
              label="Full name"
              name="display_name"
              defaultValue={account.user.display_name}
              required
              errors={errors}
            />
            <p className="account-email">
              {account.user.email}
              <span>Email address</span>
            </p>
            {(p.kind === "student" || p.kind === "instructor") && (
              <Field
                label="Institution"
                name="institution"
                defaultValue={p.institution}
                errors={errors}
              />
            )}
            {p.kind === "student" && (
              <>
                <Field
                  label="Course or program"
                  name="program"
                  defaultValue={p.program}
                  errors={errors}
                />
                <Field
                  label="Location"
                  name="location"
                  defaultValue={p.location}
                  errors={errors}
                />
                <Field label="Background" name="background" errors={errors}>
                  <textarea
                    id="background"
                    name="background"
                    rows={4}
                    maxLength={2000}
                    defaultValue={p.background}
                  />
                </Field>
                <Field
                  label="Skills"
                  name="skills"
                  defaultValue={p.skills?.join(", ")}
                  hint="Separate skills with commas, for example: Python, communication"
                  errors={errors}
                />
                <Field
                  label="Interests"
                  name="interests"
                  defaultValue={p.interests?.join(", ")}
                  hint="Separate interests with commas."
                  errors={errors}
                />
              </>
            )}
            {p.kind === "company" && (
              <>
                <Field
                  label="Company name"
                  name="company_name"
                  defaultValue={p.company_name}
                  required
                  errors={errors}
                />
                <Field
                  label="About your company"
                  name="description"
                  errors={errors}
                >
                  <textarea
                    id="description"
                    name="description"
                    maxLength={2000}
                    rows={5}
                    defaultValue={p.description}
                  />
                </Field>
                <Field
                  label="Location"
                  name="location"
                  defaultValue={p.location}
                  errors={errors}
                />
                <Field
                  label="Contact email"
                  name="contact_email"
                  type="email"
                  defaultValue={p.contact_email || ""}
                  errors={errors}
                />
                <Field
                  label="Contact phone"
                  name="contact_phone"
                  type="tel"
                  defaultValue={p.contact_phone || ""}
                  errors={errors}
                />
                <Field
                  label="Website"
                  name="website"
                  type="url"
                  defaultValue={p.website || ""}
                  errors={errors}
                />
              </>
            )}
            <div className="form-footer">
              <small>Changes are saved to your account.</small>
              <button className="primary" disabled={busy}>
                {busy ? "Saving…" : "Save profile"}
                <Check size={17} />
              </button>
            </div>
          </form>
        </section>
        <aside className="profile-aside">
          <ShieldCheck size={28} />
          <h2>{p.kind === "administrator" ? "Your account" : "Who can see this?"}</h2>
          <p>{p.kind === "company"
            ? "Keep your company details accurate for verification and for students viewing your published opportunities."
            : p.kind === "student"
              ? "Other students cannot open your private profile. Application documents are shared only with the company reviewing your submission."
              : "Your account details are used to manage your access to ThinkMedia."}</p>
          {p.kind === "student" && (
            <>
              <hr />
              <h3>Improve your suggestions</h3>
              <p>
                Add your skills and interests to support relevant opportunity
                suggestions.
              </p>
            </>
          )}
          {p.kind === "company" && (
            <>
              <hr />
              <h3>Company verification</h3>
              <span className="badge">{p.verification_status}</span>
              <p>
                Only verified companies can publish opportunities. Your
                verification status is managed by an administrator.
              </p>
            </>
          )}
        </aside>
      </div>
    </>
  );
}
function Admin() {
  const sequence = useRef(0);
  const reviewHeading = useRef<HTMLHeadingElement>(null);
  useEffect(
    () => () => {
      sequence.current++;
    },
    [],
  );
  const [items, setItems] = useState<Company[]>([]),
    [total, setTotal] = useState(0),
    [offset, setOffset] = useState(0),
    [status, setStatus] = useState("pending"),
    [error, setError] = useState(""),
    [loadError, setLoadError] = useState(false),
    [busy, setBusy] = useState(false),
    [selected, setSelected] = useState<Company | null>(null),
    [success, setSuccess] = useState("");
  useEffect(() => { if (selected) reviewHeading.current?.focus(); }, [selected]);
  async function load() {
    const request = ++sequence.current;
    setBusy(true);
    setError("");
    setLoadError(false);
    try {
      const data = await api<{ items: Company[]; total: number }>(
        `/admin/companies?status=${status}&limit=20&offset=${offset}`,
      );
      if (request !== sequence.current) return;
      setItems(data.items);
      setTotal(data.total);
    } catch (e) {
      if (request === sequence.current) {
        setError((e as Error).message);
        setLoadError(true);
      }
    } finally {
      if (request === sequence.current) setBusy(false);
    }
  }
  useEffect(() => {
    void load();
  }, [status, offset]);
  async function review(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selected) return;
    const data = Object.fromEntries(new FormData(e.currentTarget));
    setBusy(true);
    setError("");
    try {
      await api(`/admin/companies/${selected.id}/verification`, "PATCH", {
        ...data,
        expected_version: selected.verification_version,
      });
      setSelected(null);
      setSuccess("Verification decision recorded.");
      await load();
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }
  return (
    <>
      <header className="page-heading role-page-heading">
        <div>
          <h1>Company verification</h1>
          <p>Review organizations before they publish opportunities.</p>
        </div>
      </header>
      <Notice error={error} success={success} />
      <section className="panel">
        <div className="list-toolbar">
          <h2>
            Organizations {!busy && !loadError && <span className="count">{total}</span>}
          </h2>
          <label>
            Verification status{" "}
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setOffset(0);
                setSelected(null);
                setSuccess("");
              }}
            >
              <option value="pending">Pending</option>
              <option value="verified">Verified</option>
              <option value="rejected">Rejected</option>
            </select>
          </label>
        </div>
        {busy ? (
          <p role="status">Loading organizations…</p>
        ) : loadError ? (
          <div className="empty">
            <h3>Could not load organizations</h3>
            <p>Try again to see the current verification queue.</p>
            <button className="secondary" onClick={() => void load()}>Retry loading</button>
          </div>
        ) : items.length === 0 ? (
          <div className="empty">
            <ShieldCheck />
            <h3>No {status} organizations</h3>
            <p>Companies with this verification status will appear here.</p>
          </div>
        ) : (
          items.map((c) => (
            <article className="company-row verification-row" key={c.id}>
              <CompanyLogo companyId={c.id} companyName={c.company_name} />
              <div>
                <h3>{c.company_name}</h3>
                <p>{c.location || "Location not provided"}</p>
                <p>{c.description || "No company description yet."}</p>
                {c.website && (
                  <a href={c.website} target="_blank" rel="noreferrer">
                    Company website
                  </a>
                )}
              </div>
              {status === "pending" ? (
                <button className="secondary" onClick={() => setSelected(c)}>
                  Review
                  <ChevronRight size={16} />
                </button>
              ) : (
                <span className="badge">{c.verification_status}</span>
              )}
            </article>
          ))
        )}
        <div className="pagination">
          <button
            disabled={!offset || busy || loadError}
            onClick={() => { setSelected(null); setOffset(offset - 20); }}
          >
            Previous
          </button>
          <span>
            {loadError ? "Results unavailable" : total
              ? `${offset + 1}–${Math.min(offset + 20, total)} of ${total}`
              : "0 organizations"}
          </span>
          <button
            disabled={offset + 20 >= total || busy || loadError}
            onClick={() => { setSelected(null); setOffset(offset + 20); }}
          >
            Next
          </button>
        </div>
      </section>
      {selected && (
        <section className="panel review-panel">
          <h2 ref={reviewHeading} tabIndex={-1}>Review {selected.company_name}</h2>
          <p className="preserve-lines">
            {selected.description || "No description supplied."}
          </p>
          <dl className="receipt">
            <dt>Location</dt>
            <dd>{selected.location || "Not supplied"}</dd>
            <dt>Contact email</dt>
            <dd>{selected.contact_email || "Not supplied"}</dd>
            <dt>Contact phone</dt>
            <dd>{selected.contact_phone || "Not supplied"}</dd>
          </dl>
          <p>
            Confirm the evidence under your verification procedure before
            recording a decision.
          </p>
          <form onSubmit={review}>
            <Field label="Decision" name="status">
              <select id="status" name="status" defaultValue="" required>
                <option value="" disabled>Choose a decision</option>
                <option value="verified">Verify company</option>
                <option value="rejected">Reject verification</option>
              </select>
            </Field>
            <Field
              label="Reason for decision"
              name="reason"
              required
              hint="This reason is retained in the audit history."
            />
            <div className="actions">
              <button
                type="button"
                className="secondary"
                onClick={() => setSelected(null)}
              >
                Cancel
              </button>
              <button disabled={busy} className="primary">
                Confirm decision
              </button>
            </div>
          </form>
        </section>
      )}
    </>
  );
}
function Audit() {
  type Event = {
    id: string;
    action: string;
    reason?: string;
    detail?: string;
    created_at: string;
    actor_id: string;
  };
  const [verification, setVerification] = useState<Event[]>([]),
    [content, setContent] = useState<Event[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(true),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    setBusy(true);
    setError("");
    setVerification([]);
    setContent([]);
    Promise.allSettled([
      api<{ items: Event[] }>("/admin/audit-events"),
      api<{ items: Event[] }>("/admin/content-events"),
    ]).then((results) => {
      if (!active) return;
      results.forEach((result, i) => {
        if (result.status === "fulfilled")
          (i === 0 ? setVerification : setContent)(result.value.items);
        else setError(result.reason.message);
      });
      setBusy(false);
    });
    return () => {
      active = false;
    };
  }, [revision]);
  const events = (rows: Event[]) =>
    rows.length ? (
      rows.map((r) => (
        <article className="company-row" key={r.id}>
          <div>
            <h3>{r.action}</h3>
            <p>{r.reason || r.detail}</p>
            <small>
              {manila(r.created_at)} · Actor {r.actor_id}
            </small>
          </div>
        </article>
      ))
    ) : (
      <p className="muted">No recent events to display.</p>
    );
  return (
    <>
      <header className="page-heading role-page-heading">
        <div>
          <h1>Audit history</h1>
          <p>Recent privileged actions. Times shown in Asia/Manila.</p>
        </div>
      </header>
      <Notice error={error} />
      {error && <button className="secondary" onClick={() => setRevision((value) => value + 1)}>Retry audit history</button>}
      {busy && <p role="status">Loading audit history…</p>}
      {!busy && !error && <>
      <section className="panel">
        <h2>Company verification</h2>
        {events(verification)}
      </section>
      <section className="panel review-panel">
        <h2>Content and moderation</h2>
        {events(content)}
      </section>
      </>}
      <Operations />
    </>
  );
}
function navIcon(page: string): IconName {
  const names: Record<string, IconName> = {
    overview: "home",
    review: "applications",
    assistant: "guidance",
    learning: "learning",
    opportunities: "opportunities",
    applications: "applications",
    suggestions: "suggestions",
    verification: "verification",
    content: "content",
    reports: "reports",
    audit: "audit",
  };
  return names[page] || "home";
}
// FR10 / NFR05,09: keep guidance available throughout the signed-in workspace.
function GuidanceBubble() {
  const [open, setOpen] = useState(false);
  const [started, setStarted] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const close = () => {
    setOpen(false);
    trigger.current?.focus();
  };
  return (
    <div className="guidance-bubble" onKeyDown={(event) => { if (event.key === "Escape" && open) close(); }}>
      <section id="floating-guidance" className="guidance-bubble-panel" aria-label="OJT guidance" hidden={!open}>
        <div className="guidance-bubble-header">
          <strong>OJT guidance</strong>
          <button type="button" aria-label="Close guidance" onClick={close}><X size={20} /></button>
        </div>
        <div className="guidance-bubble-content">{started && <Assistant />}</div>
      </section>
      <button ref={trigger} type="button" className="guidance-bubble-trigger" aria-expanded={open} aria-controls="floating-guidance" onClick={() => { setStarted(true); setOpen(!open); }}>
        <ThinkIcon name="guidance" size={24} /> <span>{open ? "Close guidance" : "Ask guidance"}</span>
      </button>
    </div>
  );
}
function App() {
  const { route, navigate } = useRoute();
  const [welcomeOpen, setWelcomeOpen] = useState(() => !hasSeenWelcome());
  const [authMode, setAuthMode] = useState<"signup" | "signin">("signin");
  const [sidebarPreference, setSidebarPreference] = useState(
    readSidebarPreference,
  );
  const [sidebarHovered, setSidebarHovered] = useState(false);
  const [sidebarFocused, setSidebarFocused] = useState(false);
  const [railTooltip, setRailTooltip] = useState<{
    label: string;
    left: number;
    top: number;
  } | null>(null);
  function replayWelcome() {
    setMenu(false);
    setWelcomeOpen(true);
  }
  const menuTrigger = useRef<HTMLButtonElement | null>(null);
  function openMenu(e: React.MouseEvent<HTMLButtonElement>) {
    menuTrigger.current = e.currentTarget;
    setMenu(true);
  }
  const [mobile, setMobile] = useState(
      () => window.matchMedia("(max-width:720px)").matches,
    ),
    [account, setAccount] = useState<Account | null>(null),
    [loading, setLoading] = useState(true),
    [startupError, setStartupError] = useState(""),
    [menu, setMenu] = useState(false),
    [error, setError] = useState("");
  const automaticSidebar =
    sidebarPreference === null || sidebarPreference === "auto";
  const railCollapsed =
    !mobile &&
    (sidebarPreference === "collapsed" ||
      (automaticSidebar && !sidebarHovered && !sidebarFocused));
  function toggleSidebar() {
    const next = railCollapsed ? "expanded" : "collapsed";
    setSidebarPreference(next);
    saveSidebarPreference(next);
    setRailTooltip(null);
  }
  function toggleSidebarLock() {
    const next = automaticSidebar
      ? railCollapsed
        ? "collapsed"
        : "expanded"
      : "auto";
    setSidebarPreference(next);
    saveSidebarPreference(next);
    setRailTooltip(null);
  }
  function describeRailControl(e: React.SyntheticEvent<HTMLElement>) {
    if (!railCollapsed) return;
    if ((e.target as Element).closest(".rail-tooltip")) return;
    const control = (e.target as Element).closest<HTMLElement>(
      "[data-rail-label]",
    );
    if (!control) {
      // Keep the label while the pointer crosses the rail padding to reach it.
      // Leaving the sidebar (including its tooltip) still dismisses it.
      return;
    }
    const rect = control.getBoundingClientRect();
    const label = control.dataset.railLabel || "";
    setRailTooltip((current) =>
      current?.label === label
        ? current
        : {
            label,
            left: rect.right + 12,
            top: Math.max(
              22,
              Math.min(innerHeight - 22, rect.top + rect.height / 2),
            ),
          },
    );
  }
  useEffect(() => {
    const media = window.matchMedia("(max-width:720px)");
    const update = () => {
      setMobile(media.matches);
      setSidebarHovered(false);
      setSidebarFocused(false);
      setRailTooltip(null);
      if (!media.matches) setMenu(false);
    };
    media.addEventListener("change", update);
    return () => {
      media.removeEventListener("change", update);
    };
  }, []);
  async function session() {
    setLoading(true);
    setStartupError("");
    try {
      setAccount(await api<Account>("/auth/me"));
    } catch (e) {
      if (!(e instanceof ApiError && e.status === 401))
        setStartupError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void session();
  }, []);
  useEffect(() => {
    if (!railTooltip) return;
    const dismiss = (event: KeyboardEvent) => {
      if (event.key === "Escape") setRailTooltip(null);
    };
    document.addEventListener("keydown", dismiss);
    return () => document.removeEventListener("keydown", dismiss);
  }, [!!railTooltip]);
  useEffect(() => {
    if (!menu || !mobile) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.querySelector<HTMLButtonElement>(".mobile-close")?.focus();
    const keyboard = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenu(false);
      if (e.key === "Tab") {
        const controls = [
          ...document.querySelectorAll<HTMLElement>(
            ".sidebar a,.sidebar button",
          ),
        ].filter((el) => el.offsetParent !== null);
        const first = controls[0],
          last = controls[controls.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", keyboard);
    return () => {
      document.removeEventListener("keydown", keyboard);
      document.body.style.overflow = previousOverflow;
      if (window.matchMedia("(max-width:720px)").matches)
        menuTrigger.current?.focus();
      else
        document.querySelector<HTMLButtonElement>(".sidebar-toggle")?.focus();
    };
  }, [menu, mobile]);
  useEffect(() => {
    if (account)
      requestAnimationFrame(() => {
        window.scrollTo(0, 0);
        document
          .getElementById("main")
          ?.focus({ preventScroll: true });
      });
  }, [route.page, route.id]);
  if (welcomeOpen)
    return (
      <Onboarding
        signedIn={!!account}
        onComplete={(destination) => {
          markWelcomeSeen();
          setAuthMode(destination);
          setWelcomeOpen(false);
        }}
      />
    );
  if (loading)
    return (
      <main className="boot" role="status">
        <GraduationCap size={36} />
        <p>Loading your account…</p>
      </main>
    );
  if (startupError)
    return (
      <main className="boot">
        <GraduationCap size={36} />
        <h1>ThinkMedia could not connect</h1>
        <Notice error={startupError} />
        <button className="primary" onClick={session}>
          Try again
        </button>
      </main>
    );
  if (!account)
    return (
      <Auth
        key={authMode}
        initialMode={authMode}
        onReplay={replayWelcome}
        onLogin={(a) => {
          setAccount(a);
          setMenu(false);
          navigate("overview");
        }}
      />
    );
  const admin = account.user.role === "administrator",
    company = account.user.role === "company",
    student = account.user.role === "student";
  const nav = [
    { id: "overview", label: "Home", short: "Home", icon: LayoutDashboard },
    ...(!company && !admin
      ? [
          {
            id: "learning",
            label: "Learning",
            short: "Learning",
            icon: BookOpen,
          },
        ]
      : []),
    ...(!admin
      ? [
          {
            id: "opportunities",
            label: company ? "My listings" : "Opportunities",
            short: company ? "Listings" : "OJT",
            icon: BriefcaseBusiness,
          },
        ]
      : []),
    ...(student
      ? [
          {
            id: "applications",
            label: "My applications",
            short: "Applications",
            icon: FileText,
          },
          {
            id: "suggestions",
            label: "Suggestions",
            short: "For you",
            icon: Sparkles,
          },
        ]
      : []),
    ...(company
      ? [
          {
            id: "review",
            label: "Applicants",
            short: "Applicants",
            icon: FileText,
          },
        ]
      : []),
    ...(admin
      ? [
          {
            id: "verification",
            label: "Company verification",
            short: "Verify",
            icon: ShieldCheck,
          },
          {
            id: "content",
            label: "Learning content",
            short: "Content",
            icon: BookOpen,
          },
          {
            id: "reports",
            label: "Content reports",
            short: "Reports",
            icon: FileText,
          },
          {
            id: "audit",
            label: "Audit history",
            short: "Audit",
            icon: ClipboardList,
          },
        ]
      : []),
  ];
  const profileLabel = company ? "Company profile" : "My profile";
  const allowed = [...nav.map((n) => n.id), "profile", "more", "assistant"];
  const page = allowed.includes(route.page) ? route.page : "overview";
  const quickIds = admin
    ? ["overview", "verification", "content", "reports"]
    : company
      ? ["overview", "opportunities", "review"]
      : student
        ? ["overview", "learning", "opportunities", "applications"]
        : ["overview", "learning", "opportunities"];
  const quick = nav.filter((n) => quickIds.includes(n.id));
  async function logout() {
    try {
      await api("/auth/logout", "POST");
      setAccount(null);
      setMenu(false);
      navigate("overview");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <div
      className={`app-shell ${railCollapsed ? "sidebar-is-collapsed" : ""} ${automaticSidebar ? "sidebar-is-auto" : "sidebar-is-locked"}`}
    >
      <a
        href="#main"
        className="skip"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main")?.focus();
        }}
      >
        Skip to content
      </a>
      {mobile && menu && (
        <button
          className="nav-backdrop"
          tabIndex={-1}
          aria-label="Dismiss navigation"
          onClick={() => setMenu(false)}
        />
      )}
      <aside
        id="main-sidebar"
        onPointerEnter={(e) => {
          if (e.pointerType === "mouse") setSidebarHovered(true);
        }}
        onMouseOver={describeRailControl}
        onMouseLeave={() => {
          setRailTooltip(null);
          setSidebarHovered(false);
        }}
        onFocusCapture={(e) => {
          setSidebarFocused(e.target.matches(":focus-visible"));
          describeRailControl(e);
        }}
        onBlurCapture={(e) => {
          setRailTooltip(null);
          if (!e.currentTarget.contains(e.relatedTarget))
            setSidebarFocused(false);
        }}
        onScrollCapture={() => setRailTooltip(null)}
        role={mobile && menu ? "dialog" : undefined}
        aria-modal={mobile && menu ? true : undefined}
        aria-label={mobile && menu ? "Navigation drawer" : undefined}
        inert={mobile && !menu ? true : undefined}
        className={`sidebar ${menu ? "open" : ""}`}
      >
        <a
          className="brand"
          aria-label="ThinkMedia home"
          data-rail-label="ThinkMedia home"
          href={href("overview")}
          onClick={() => setMenu(false)}
        >
          <BrandMark />
          <span>
            ThinkMedia<span className="brand-dot">.</span>
          </span>
        </a>
        <button
          aria-label="Close navigation"
          className="mobile-close"
          onClick={() => setMenu(false)}
        >
          <X />
        </button>
        <p className="portal-label">
          {admin
            ? "Administration"
            : company
              ? "Company portal"
              : account.user.role === "instructor"
                ? "Instructor portal"
                : "Student portal"}
        </p>
        <div className="sidebar-controls">
          <span className="sidebar-mode-label">
            {automaticSidebar ? "Auto-expand" : "Locked"}
          </span>
          <button
            type="button"
            className="sidebar-toggle"
            aria-label={railCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!railCollapsed}
            aria-controls="main-sidebar"
            title={
              railCollapsed
                ? "Expand and lock sidebar"
                : "Collapse and lock sidebar"
            }
            onClick={toggleSidebar}
          >
            {railCollapsed ? (
              <PanelLeftOpen size={19} />
            ) : (
              <PanelLeftClose size={19} />
            )}
          </button>
          <button
            type="button"
            className="sidebar-lock"
            aria-label={automaticSidebar ? "Lock sidebar" : "Unlock sidebar"}
            aria-pressed={!automaticSidebar}
            title={
              automaticSidebar
                ? "Lock the current sidebar width"
                : "Unlock to expand on hover or keyboard focus"
            }
            onClick={toggleSidebarLock}
          >
            {automaticSidebar ? <PinOff size={18} /> : <Pin size={18} />}
          </button>
        </div>
        <nav aria-label="Main navigation">
          {nav.map((n) => (
            <a
              key={n.id}
              aria-label={n.label}
              data-rail-label={n.label}
              href={href(n.id)}
              className={page === n.id ? "active" : ""}
              aria-current={page === n.id ? "page" : undefined}
              onClick={() => setMenu(false)}
            >
              <ThinkIcon name={navIcon(n.id)} size={22} />
              <span className="rail-label">{n.label}</span>
            </a>
          ))}
        </nav>
        <div className="sidebar-account">
          <a
            href={href("profile")}
            aria-label={
              railCollapsed
                ? `${account.user.display_name} ${profileLabel}`
                : undefined
            }
            data-rail-label={`${profileLabel} · ${account.user.display_name}`}
            className={
              page === "profile" ? "account-link active" : "account-link"
            }
            onClick={() => setMenu(false)}
          >
            <span className="avatar" aria-hidden="true">
              {account.user.display_name.slice(0, 1)}
            </span>
            <span className="account-info">
              <strong>{account.user.display_name}</strong>
              <small>{profileLabel}</small>
            </span>
            <UserRound size={17} />
          </a>
          <button
            className="getting-started"
            aria-label="Getting started"
            data-rail-label="Getting started"
            onClick={replayWelcome}
          >
            <ThinkIcon name="guidance" size={19} />
            <span className="rail-label">Getting started</span>
          </button>
          <button
            className="sign-out"
            aria-label="Sign out"
            data-rail-label="Sign out"
            onClick={logout}
          >
            <LogOut size={17} />
            <span className="rail-label">Sign out</span>
          </button>
        </div>
        {railCollapsed && railTooltip && (
          <div
            className="rail-tooltip"
            role="tooltip"
            style={{ left: railTooltip.left, top: railTooltip.top }}
          >
            {railTooltip.label}
          </div>
        )}
      </aside>
      <div className="workspace" inert={mobile && menu ? true : undefined}>
        <header className="topbar mobile-header">
          <button
            className="mobile-toggle"
            aria-label="Open navigation"
            onClick={openMenu}
          >
            <Menu />
          </button>
          <a className="mobile-brand" href={href("overview")}>
            <BrandMark size={28} />
            ThinkMedia<span>.</span>
          </a>
        </header>
        <main id="main" className={`main-content ${admin || company ? "role-workspace" : ""}`} tabIndex={-1}>
          <Notice error={error} />
          {page === "more" ? (
            <section className="more-page" aria-labelledby="more-title">
              <header className="page-heading">
                <div>
                  <h1 id="more-title">More</h1>
                  <p>Your workspace and account, in one place.</p>
                </div>
              </header>
              <a className="more-account" href={href("profile")}>
                <span className="avatar" aria-hidden="true">
                  {account.user.display_name.slice(0, 1)}
                </span>
                <span>
                  <strong>{account.user.display_name}</strong>
                  <small>{profileLabel}</small>
                </span>
                <ChevronRight size={20} aria-hidden="true" />
              </a>
              <nav
                className="more-destinations"
                aria-label="Workspace destinations"
              >
                <h2>Your workspace</h2>
                <div className="more-menu-list">
                  {nav.map((n) => (
                    <a href={href(n.id)} key={n.id}>
                      <ThinkIcon name={navIcon(n.id)} size={24} />
                      <span>{n.label}</span>
                      <ChevronRight size={18} aria-hidden="true" />
                    </a>
                  ))}
                </div>
              </nav>
              <section
                className="more-account-actions"
                aria-labelledby="more-account-title"
              >
                <h2 id="more-account-title">Account</h2>
                <div className="more-menu-list">
                  <button type="button" onClick={replayWelcome}>
                    <ThinkIcon name="guidance" size={24} />
                    <span>Getting started</span>
                    <ChevronRight size={18} aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    className="more-sign-out"
                    onClick={logout}
                  >
                    <LogOut size={23} aria-hidden="true" />
                    <span>Sign out</span>
                  </button>
                </div>
              </section>
            </section>
          ) : page === "profile" ? (
            <Profile account={account} onSave={setAccount} />
          ) : page === "verification" ? (
            <Admin />
          ) : page === "audit" ? (
            <Audit />
          ) : page === "suggestions" ? (
            <Recommendations
              account={account}
              onProfile={() => navigate("profile")}
              onOpen={(kind, id) =>
                navigate(kind === "listing" ? "opportunities" : "learning", id)
              }
            />
          ) : page === "assistant" ? (
            <Assistant />
          ) : ["learning", "content", "reports"].includes(page) ? (
            <Learning
              key={page}
              admin={admin}
              reports={page === "reports"}
              personalized={student}
              initialId={route.id}
              onSelect={(id) => navigate(page, id)}
            />
          ) : ["opportunities", "applications", "review"].includes(page) ? (
            <Marketplace
              key={page}
              account={account}
              mode={
                page === "applications"
                  ? "applications"
                  : page === "review"
                    ? "review"
                    : company
                      ? "company"
                      : "browse"
              }
              initialId={page === "opportunities" ? route.id : undefined}
              initialFilters={route.filters}
              onFilters={(filters) => {
                window.location.hash =
                  href("opportunities") + (filters ? "?" + filters : "");
              }}
              initialApplicationId={
                page !== "opportunities" ? route.id : undefined
              }
              onListing={(id) => {
                window.location.hash =
                  href("opportunities", id) +
                  (route.query ? "?" + route.query : "");
              }}
              onApplication={(id) =>
                navigate(company ? "review" : "applications", id)
              }
            />
          ) : (
            <Home account={account} />
          )}
          <div className="workspace-demo-note">
            <LocalDemoNotice />
          </div>
        </main>
        <nav className="mobile-task-nav" aria-label="Quick navigation">
          {quick.map((n) => (
            <a
              href={href(n.id)}
              aria-label={
                n.id === "opportunities" && !company
                  ? "OJT opportunities"
                  : n.label
              }
              key={n.id}
              aria-current={page === n.id ? "page" : undefined}
              className={page === n.id ? "active" : ""}
            >
              <ThinkIcon name={navIcon(n.id)} size={24} />
              <span>{n.short}</span>
            </a>
          ))}
          <a
            href={href("more")}
            aria-label="More navigation"
            aria-current={page === "more" ? "page" : undefined}
            className={page === "more" ? "active" : ""}
          >
            <Menu size={21} />
            <span>More</span>
          </a>
        </nav>
        {page !== "assistant" && <GuidanceBubble />}
      </div>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
