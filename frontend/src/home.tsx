// FR01–11 / W02–W08: the dashboard reflects real role-specific work, not demo metrics.
import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardList,
  FileText,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { Account, api, Company, manila } from "./api";
import type { Application, Listing } from "./marketplace";
import { href } from "./navigation";
import { StatusBadge } from "./status";
import { StudentHome } from "./student-home";
import { WelcomeArt, ThinkIcon, type IconName } from "./brand";
import { RoleHome } from "./role-home";
type Resource = { id: string; title: string; summary: string; tags: string[] };
type Report = { id: string; reason: string; created_at: string };
type Page<T> = { items: T[]; total: number };
export function Home({ account }: { account: Account }) {
  if (account.user.role === "student") return <StudentHome account={account} />;
  if (account.user.role === "company" || account.user.role === "administrator") return <RoleHome account={account} />;
  return <InstructorHome account={account} />;
}
function InstructorHome({ account }: { account: Account }) {
  const [applications, setApplications] = useState<Page<Application> | null>(
      null,
    ),
    [listings, setListings] = useState<Page<Listing> | null>(null),
    [resources, setResources] = useState<Page<Resource> | null>(null),
    [companies, setCompanies] = useState<Page<Company> | null>(null),
    [reports, setReports] = useState<Page<Report> | null>(null),
    [busy, setBusy] = useState(true),
    [error, setError] = useState(""),
    [revision, setRevision] = useState(0);
  const role = account.user.role,
    student = role === "student",
    company = role === "company",
    admin = role === "administrator";
  useEffect(() => {
    let active = true;
    setBusy(true);
    setError("");
    if (role === "student") {
      setBusy(false);
      return;
    }
    const jobs: Promise<void>[] = [];
    const get = <T,>(path: string, update: (data: Page<T>) => void) =>
      api<Page<T>>(path).then((data) => {
        if (active) update(data);
      });
    if (student || company)
      jobs.push(
        get<Application>(
          `${company ? "/company/applications" : "/applications/me"}?limit=4`,
          setApplications,
        ),
      );
    if (company)
      jobs.push(get<Listing>("/company/listings?limit=4", setListings));
    if (admin) {
      jobs.push(
        get<Company>("/admin/companies?status=pending&limit=3", setCompanies),
      );
      jobs.push(
        get<Report>("/admin/reports?status=pending&limit=3", setReports),
      );
    }
    if (!company && !admin)
      jobs.push(get<Resource>("/content?limit=3", setResources));
    Promise.allSettled(jobs).then((results) => {
      if (!active) return;
      if (results.some((r) => r.status === "rejected"))
        setError(
          "Some recent activity could not be loaded. You can still use the navigation to open your work.",
        );
      setBusy(false);
    });
    return () => {
      active = false;
    };
  }, [role, revision]);
  const profileMissing = student
    ? !account.profile.program || !account.profile.skills?.length
    : role === "instructor"
      ? !account.profile.institution
      : false;
  const title = admin
    ? "Administration"
    : company
      ? "Company dashboard"
      : `Hello, ${account.user.display_name.split(" ")[0]}.`;
  const empty = (
    heading: string,
    body: string,
    link: string,
    label: string,
  ) => (
    <div className="work-empty">
      <FileText size={25} />
      <h3>{heading}</h3>
      <p>{body}</p>
      <a className="secondary" href={link}>
        {label}
        <ArrowRight size={16} />
      </a>
    </div>
  );
  const appRows = applications?.items.map((a) => (
    <a
      className="activity-row"
      key={a.id}
      href={href(company ? "review" : "applications", a.id)}
    >
      <div>
        <strong>{company ? a.student_name : a.listing_title}</strong>
        <span>{company ? a.listing_title : a.company_name}</span>
        <small>{manila(a.created_at)}</small>
      </div>
      <StatusBadge status={a.status} />
      <ArrowRight size={16} />
    </a>
  ));
  if (student) return <StudentHome account={account} />;
  return (
    <>
      <header className={admin || company ? "page-heading role-dashboard-heading" : "page-heading dashboard-heading illustrated-welcome"}>
        <div>
          <h1>{title}</h1>
          <p>
            {admin
              ? "Keep the platform trustworthy. Review company accounts, learning resources and reports."
              : company
                ? "Manage your listings and follow up on applications."
                : student
                  ? "Find OJT opportunities, prepare your requirements and follow your applications."
                  : "Browse learning resources and opportunities to guide your students."}
          </p>
        </div>
        <a
          className="primary"
          href={href(admin ? "verification" : "opportunities")}
        >
          {admin
            ? "Review companies"
            : company
              ? "View my listings"
              : "Find opportunities"}
          <ArrowRight size={17} />
        </a>
        {!admin && !company && <WelcomeArt className="dashboard-illustration" />}
      </header>
      {error && (
        <div className="notice error" role="alert">
          <div>
            {error}
            <button
              className="text-button"
              onClick={() => setRevision(revision + 1)}
            >
              Reload activity
            </button>
          </div>
        </div>
      )}
      {profileMissing && (
        <div className="profile-nudge">
          <UserRound size={20} />
          <div>
            <strong>
              {student ? "Add your course and skills" : "Add your institution"}
            </strong>
            <p>
              {student
                ? "A few profile details help us suggest relevant opportunities."
                : "Keep your institution visible in your account details."}
            </p>
          </div>
          <a href={href("profile")}>
            Complete your profile
            <ArrowRight size={15} />
          </a>
        </div>
      )}
      {company && account.profile.verification_status !== "verified" && (
        <div className="verification-banner">
          <ShieldCheck size={24} />
          <div>
            <strong>
              Company verification: {account.profile.verification_status}
            </strong>
            <p>
              {account.profile.verification_status === "rejected"
                ? "Your company was not verified. Review your organization details with the administrator."
                : "An administrator needs to verify your company before you can create and publish listings."}
            </p>
          </div>
          <a className="secondary" href={href("profile")}>
            View profile
          </a>
        </div>
      )}
      <div className={`dashboard-grid ${admin ? "admin-dashboard-grid" : ""}`}>
        <div className="dashboard-main">
          {admin ? (
            <section className="work-section">
              <div className="section-title">
                <h2>
                  Companies awaiting verification
                  {companies && (
                    <span className="queue-count">{companies.total}</span>
                  )}
                </h2>
                <a href={href("verification")}>
                  Open queue
                  <ArrowRight size={15} />
                </a>
              </div>
              {busy ? (
                <p className="loading-line" role="status">
                  Loading company reviews…
                </p>
              ) : companies?.items.length ? (
                companies.items.map((c) => (
                  <a
                    className="activity-row"
                    key={c.id}
                    href={href("verification")}
                  >
                    <div>
                      <strong>{c.company_name}</strong>
                      <span>{c.location || "Location not supplied"}</span>
                    </div>
                    <StatusBadge status={c.verification_status} />
                    <ArrowRight size={16} />
                  </a>
                ))
              ) : (
                companies &&
                empty(
                  "No companies waiting",
                  "New company registrations appear here for review.",
                  href("verification"),
                  "View verification queue",
                )
              )}
            </section>
          ) : company ? (
            <section className="work-section">
              <div className="section-title">
                <h2>
                  Your listings
                  {listings && (
                    <span className="queue-count">{listings.total}</span>
                  )}
                </h2>
                <a href={href("opportunities")}>
                  View all
                  <ArrowRight size={15} />
                </a>
              </div>
              {busy ? (
                <p className="loading-line" role="status">
                  Loading listings…
                </p>
              ) : listings?.items.length ? (
                listings.items.map((l) => (
                  <a
                    className="activity-row"
                    href={href("opportunities", l.id)}
                    key={l.id}
                  >
                    <div>
                      <strong>{l.title}</strong>
                      <span>
                        {l.location} · {l.type === "ojt" ? "OJT" : "Job"}
                      </span>
                    </div>
                    <StatusBadge status={l.status} />
                    <ArrowRight size={16} />
                  </a>
                ))
              ) : (
                listings &&
                empty(
                  "No listings yet",
                  account.profile.verification_status === "verified"
                    ? "Create a draft with the role, location and requirements."
                    : "Complete your company profile while you wait for verification.",
                  href(
                    account.profile.verification_status === "verified"
                      ? "opportunities"
                      : "profile",
                  ),
                  account.profile.verification_status === "verified"
                    ? "Manage listings"
                    : "Complete company profile",
                )
              )}
            </section>
          ) : student ? (
            <section className="work-section">
              <div className="section-title">
                <h2>
                  Your applications
                  {applications && (
                    <span className="queue-count">{applications.total}</span>
                  )}
                </h2>
                <a href={href("applications")}>
                  View all
                  <ArrowRight size={15} />
                </a>
              </div>
              {busy ? (
                <p className="loading-line" role="status">
                  Loading applications…
                </p>
              ) : applications?.items.length ? (
                appRows
              ) : (
                applications &&
                empty(
                  "No applications yet",
                  "Find an open opportunity, check the requirements and submit your PDF.",
                  href("opportunities"),
                  "Browse opportunities",
                )
              )}
            </section>
          ) : (
            <section className="work-section">
              <div className="section-title">
                <h2>Learning resources</h2>
                <a href={href("learning")}>
                  Browse learning
                  <ArrowRight size={15} />
                </a>
              </div>
              {busy ? (
                <p role="status">Loading learning resources…</p>
              ) : resources?.items.length ? (
                resources.items.map((r) => (
                  <a
                    className="resource-home-row"
                    href={href("learning", r.id)}
                    key={r.id}
                  >
                    <BookOpen size={20} />
                    <div>
                      <strong>{r.title}</strong>
                      <p>{r.summary}</p>
                    </div>
                    <ArrowRight size={16} />
                  </a>
                ))
              ) : (
                resources &&
                empty(
                  "No published resources yet",
                  "Approved lessons and preparation tips will appear here.",
                  href("learning"),
                  "Open learning",
                )
              )}
            </section>
          )}
          {company && (
            <section className="work-section">
              <div className="section-title">
                <h2>
                  Recent applicants
                  {applications && (
                    <span className="queue-count">{applications.total}</span>
                  )}
                </h2>
                <a href={href("review")}>
                  Review applicants
                  <ArrowRight size={15} />
                </a>
              </div>
              {busy ? (
                <p role="status">Loading applicants…</p>
              ) : applications?.items.length ? (
                appRows
              ) : (
                applications &&
                empty(
                  "No applications to review",
                  "Students can apply once you publish an open listing.",
                  href("opportunities"),
                  "View your listings",
                )
              )}
            </section>
          )}
          {admin && (
            <section className="work-section">
              <div className="section-title">
                <h2>
                  Reported content
                  {reports && (
                    <span className="queue-count">{reports.total}</span>
                  )}
                </h2>
                <a href={href("reports")}>
                  Open reports
                  <ArrowRight size={15} />
                </a>
              </div>
              {busy ? (
                <p role="status">Loading reports…</p>
              ) : reports?.items.length ? (
                reports.items.map((r) => (
                  <a className="activity-row" key={r.id} href={href("reports")}>
                    <div>
                      <strong>{r.reason}</strong>
                      <span>{manila(r.created_at)}</span>
                    </div>
                    <span className="status-badge status-pending">
                      Needs review
                    </span>
                    <ArrowRight size={16} />
                  </a>
                ))
              ) : (
                reports &&
                empty(
                  "No unresolved reports",
                  "Reports from learners appear here for moderation.",
                  href("content"),
                  "Review learning content",
                )
              )}
            </section>
          )}
          {student && (
            <section className="work-section">
              <div className="section-title">
                <h2>Prepare for OJT</h2>
                <a href={href("learning")}>
                  All resources
                  <ArrowRight size={15} />
                </a>
              </div>
              {busy ? (
                <p role="status">Loading preparation resources…</p>
              ) : resources?.items.length ? (
                resources.items.map((r) => (
                  <a
                    className="resource-home-row"
                    href={href("learning", r.id)}
                    key={r.id}
                  >
                    <BookOpen size={20} />
                    <div>
                      <strong>{r.title}</strong>
                      <p>{r.summary}</p>
                    </div>
                    <ArrowRight size={16} />
                  </a>
                ))
              ) : (
                resources &&
                empty(
                  "No published resources yet",
                  "Approved lessons, interview tips and short quizzes will appear here.",
                  href("learning"),
                  "Open learning",
                )
              )}
            </section>
          )}
        </div>
        <aside className="dashboard-side">
          <section className="work-section">
            <h2>
              {admin
                ? "Review tools"
                : company
                  ? "Company information"
                  : "Preparation and profile"}
            </h2>
            {(admin
              ? [
                  [
                    "verification",
                    "Verify companies",
                    "Check organization details before publication.",
                    ShieldCheck,
                  ],
                  [
                    "content",
                    "Manage learning content",
                    "Prepare and publish approved resources.",
                    BookOpen,
                  ],
                  [
                    "audit",
                    "Audit history",
                    "See recorded verification and moderation actions.",
                    ClipboardList,
                  ],
                ]
              : company
                ? [
                    [
                      "profile",
                      "Company profile",
                      "Update your organization and contact details.",
                      UserRound,
                    ],
                    [
                      "review",
                      "Applicant review",
                      "Open submissions to your own listings.",
                      ClipboardList,
                    ],
                    [
                      "assistant",
                      "Preparation resources",
                      "Look up approved OJT and platform guidance.",
                      BookOpen,
                    ],
                  ]
                : [
                    [
                      "opportunities",
                      "Find an opportunity",
                      "Filter by location, type and skills.",
                      BriefcaseBusiness,
                    ],
                    [
                      "suggestions",
                      "Suggestions for you",
                      "Explore matches based on your profile.",
                      CheckCircle2,
                    ],
                    [
                      "assistant",
                      "Ask a preparation question",
                      "Read approved sources for your question.",
                      BookOpen,
                    ],
                  ]
            )
              .filter(
                ([page]) => role !== "instructor" || page !== "suggestions",
              )
              .map(([page, label, description, Icon]) => {
                const icons: Record<string, IconName> = {
                  verification: "verification",
                  content: "learning",
                  audit: "audit",
                  profile: "profile",
                  review: "applications",
                  assistant: "guidance",
                  opportunities: "opportunities",
                  suggestions: "suggestions",
                };
                void Icon;
                return (
                  <a
                    className="next-task"
                    href={href(String(page))}
                    key={String(page)}
                  >
                    <span className={`task-art task-art-${page}`}>
                      <ThinkIcon
                        name={icons[String(page)] || "learning"}
                        size={33}
                      />
                    </span>
                    <div>
                      <strong>{String(label)}</strong>
                      <span>{String(description)}</span>
                    </div>
                    <ArrowRight size={15} />
                  </a>
                );
              })}
          </section>
          <section className="privacy-note">
            <ShieldCheck size={19} />
            <p>
              {admin
                ? "Verification and moderation decisions are recorded with your account and time."
                : company
                  ? "Applicant documents are private to the applicant and your company."
                  : "Your documents are shared only with the company reviewing your application."}
            </p>
          </section>
        </aside>
      </div>
      {admin && (
        <section className="admin-role-guide" aria-labelledby="admin-role-guide-title">
          <div className="admin-role-guide-intro">
            <ShieldCheck size={27} aria-hidden="true" />
            <div><h2 id="admin-role-guide-title">How opportunities reach students</h2><p>Each account has a different part to play.</p></div>
          </div>
          <div className="admin-role-steps">
            <div><span className="admin-role-icon"><ShieldCheck size={22} /></span><div><strong>Administrator</strong><p>Reviews and verifies company accounts.</p></div></div>
            <div><span className="admin-role-icon"><BriefcaseBusiness size={22} /></span><div><strong>Company</strong><p>Creates and publishes its own opportunities after verification.</p></div></div>
            <div><span className="admin-role-icon"><UserRound size={22} /></span><div><strong>Student</strong><p>Finds opportunities and applies directly.</p></div></div>
          </div>
        </section>
      )}
    </>
  );
}
