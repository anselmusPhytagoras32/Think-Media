// FR02/06/07/11, W05/W08; NFR03/05/09: real role-owned work in the student visual system.
import { useEffect, useRef, useState } from "react";
import { useDataRevision } from "./live-data";
import { ArrowRight, Plus } from "lucide-react";
import { api, manila, type Account, type Company } from "./api";
import type { Application, Listing } from "./marketplace";
import { href } from "./navigation";
import { ThinkIcon, type IconName } from "./brand";
import { CompanyLogo } from "./company-brand";
import { StatusBadge } from "./status";
import { WorkspaceArt } from "./workspace-art";

type Page<T> = { items: T[]; total: number };
type Report = { id: string; reason: string; created_at: string };

export function RoleHome({ account }: { account: Account }) {
  const admin = account.user.role === "administrator";
  const verified = account.profile.verification_status === "verified";
  const [companies, setCompanies] = useState<Page<Company> | null>(null);
  const [reports, setReports] = useState<Page<Report> | null>(null);
  const [listings, setListings] = useState<Page<Listing> | null>(null);
  const [applications, setApplications] = useState<Page<Application> | null>(
    null,
  );
  const [busy, setBusy] = useState(true);
  const [failed, setFailed] = useState<string[]>([]);
  const [revision, setRevision] = useState(0);
  const liveRevision = useDataRevision(["accounts", "marketplace", "learning"]);
  const loaded = useRef(false);
  useEffect(() => {
    let active = true;
    setBusy(!loaded.current);
    setFailed([]);
    if (!loaded.current) { setCompanies(null); setReports(null); setListings(null); setApplications(null); }
    const get = <T,>(
      name: string,
      path: string,
      update: (value: Page<T> | null) => void,
    ) =>
      api<Page<T>>(path)
        .then((value) => {
          if (active) update(value);
        })
        .catch(() => {
        if (active) { update(null); setFailed((old) => [...old, name]); }
        });
    Promise.all(
      admin
        ? [
            get(
              "companies",
              "/admin/companies?status=pending&limit=4",
              setCompanies,
            ),
            get("reports", "/admin/reports?status=pending&limit=3", setReports),
          ]
        : [
            get("listings", "/company/listings?limit=4", setListings),
            get("applicants", "/company/applications?limit=4", setApplications),
          ],
    ).finally(() => {
      if (active) { loaded.current = true; setBusy(false); }
    });
    return () => {
      active = false;
    };
  }, [admin, revision, liveRevision]);
  const first = account.user.display_name.split(" ")[0];
  const categories: {
    title: string;
    detail: string;
    path: string;
    icon: IconName;
    tone: string;
  }[] = admin
    ? [
        {
          title: "Company reviews",
          detail: companies
            ? `${companies.total} awaiting verification`
            : "Review company accounts",
          path: href("verification"),
          icon: "verification",
          tone: "peach",
        },
        {
          title: "Learning content",
          detail: "Prepare resources for students",
          path: href("content"),
          icon: "learning",
          tone: "aqua",
        },
        {
          title: "Content reports",
          detail: reports
            ? `${reports.total} unresolved reports`
            : "Review reported resources",
          path: href("reports"),
          icon: "reports",
          tone: "pink",
        },
      ]
    : [
        {
          title: "Your listings",
          detail: listings
            ? `${listings.total} total listings`
            : "Manage your opportunities",
          path: href("opportunities"),
          icon: "listing-board",
          tone: "peach",
        },
        {
          title: "Applicants",
          detail: applications
            ? `${applications.total} applications received`
            : "Review your applications",
          path: href("review"),
          icon: "applicants",
          tone: "aqua",
        },
        {
          title: "Company profile",
          detail: "Organization and contact details",
          path: href("profile"),
          icon: "organization",
          tone: "pink",
        },
      ];
  const retry = (name: string) => (
    <div className="role-load-error" role="alert">
      <p>Could not load {name}.</p>
      <button
        type="button"
        className="text-button"
        onClick={() => setRevision((old) => old + 1)}
      >
        Retry {name}
      </button>
    </div>
  );
  return (
    <div className="role-home">
      <header className="role-home-header">
        <div>
          <h1>
            {admin ? (
              <>
                Your review <em>workspace.</em>
              </>
            ) : (
              <>
                Your company <em>workspace.</em>
              </>
            )}
          </h1>
          <p>
            <strong>Hello, {first}.</strong>{" "}
            {admin
              ? "Keep companies, resources and opportunities ready for students."
              : account.profile.company_name ||
                "Manage your opportunities and meet your applicants."}
          </p>
        </div>
        <a
          className="consumer-profile"
          href={href("profile")}
          aria-label="Open my profile"
        >
          <span>{first.slice(0, 1)}</span>
          <ThinkIcon name={admin ? "verification" : "organization"} size={25} />
        </a>
      </header>
      {!admin && !verified && (
        <section
          className="role-verification-banner"
          aria-label="Company verification status"
        >
          <ThinkIcon name="verification" size={30} />
          <div>
            <strong>
              Company verification: {account.profile.verification_status}
            </strong>
            <p>
              {account.profile.verification_status === "rejected"
                ? "Contact the administrator to review your organization details."
                : "Your account needs administrator approval before you can create or publish listings."}
            </p>
          </div>
          <a href={href("profile")}>
            View profile <ArrowRight size={16} />
          </a>
        </section>
      )}
      <nav
        className="role-destinations"
        aria-label={admin ? "Administration tasks" : "Company tasks"}
      >
        {categories.map((item) => (
          <a
            key={item.title}
            className={`role-destination role-tone-${item.tone}`}
            href={item.path}
          >
            <WorkspaceArt kind={item.icon} />
            <strong>{item.title}</strong>
            <span>{item.detail}</span>
            <ArrowRight
              className="role-destination-arrow"
              size={17}
              aria-hidden="true"
            />
          </a>
        ))}
      </nav>
      <div className="role-work-grid">
        <section
          className="role-work-list"
          aria-labelledby="role-primary-title"
        >
          <div className="role-section-heading">
            <h2 id="role-primary-title">
              {admin ? "Companies awaiting verification" : "Your listings"}
            </h2>
            <a href={href(admin ? "verification" : "opportunities")}>
              {admin ? "Review companies" : "View my listings"}
              <ArrowRight size={15} />
            </a>
          </div>
          {busy ? (
            <p className="role-loading" role="status">
              {admin ? "Loading company reviews…" : "Loading listings…"}
            </p>
          ) : failed.includes(admin ? "companies" : "listings") ? (
            retry(admin ? "companies" : "listings")
          ) : admin ? (
            companies?.items.length ? (
              <div className="role-records">
                {companies.items.map((company) => (
                  <a
                    className="role-record"
                    key={company.id}
                    href={href("verification", company.id)}
                  >
                    <CompanyLogo
                      companyId={company.id}
                      companyName={company.company_name}
                    />
                    <div>
                      <strong>{company.company_name}</strong>
                      <span>{company.location || "Location not supplied"}</span>
                    </div>
                    <StatusBadge status={company.verification_status} />
                    <ArrowRight size={16} aria-hidden="true" />
                  </a>
                ))}
              </div>
            ) : (
              <div className="role-empty">
                <WorkspaceArt kind="verification" />
                <div>
                  <h3>No companies waiting</h3>
                  <p>New registrations will appear here for review.</p>
                  <a href={href("verification")}>
                    View verification queue <ArrowRight size={15} />
                  </a>
                </div>
              </div>
            )
          ) : listings?.items.length ? (
            <div className="role-records">
              {listings.items.map((listing) => (
                <a
                  className="role-record"
                  key={listing.id}
                  href={href("opportunities", listing.id)}
                >
                  <span className="role-record-symbol">
                    <ThinkIcon name="listing-board" size={25} />
                  </span>
                  <div>
                    <strong>{listing.title}</strong>
                    <span>
                      {listing.location} ·{" "}
                      {listing.type === "ojt" ? "OJT" : "Job"}
                    </span>
                  </div>
                  <StatusBadge status={listing.status} />
                  <ArrowRight size={16} aria-hidden="true" />
                </a>
              ))}
            </div>
          ) : (
            <div className="role-empty role-empty-start">
              <WorkspaceArt kind="listing-board" />
              <div>
                <h3>No listings yet</h3>
                <p>
                  {verified
                    ? "Start with a role, location and the skills students can bring to your team."
                    : "Complete your company profile while your account is being reviewed."}
                </p>
                <a
                  className={verified ? "primary" : "secondary"}
                  href={verified ? "#/opportunities?new=1" : href("profile")}
                >
                  {verified ? (
                    <>
                      <Plus size={16} /> Create your first listing
                    </>
                  ) : (
                    <>
                      Complete company profile <ArrowRight size={16} />
                    </>
                  )}
                </a>
              </div>
            </div>
          )}
          {!admin && verified && !!listings?.items.length && (
            <a className="role-add-listing" href="#/opportunities?new=1">
              <Plus size={18} /> Create another listing
            </a>
          )}
        </section>
        <section
          className="role-work-list role-secondary-work"
          aria-labelledby="role-secondary-title"
        >
          <div className="role-section-heading">
            <h2 id="role-secondary-title">
              {admin ? "Reported content" : "Recent applicants"}
            </h2>
            <a href={href(admin ? "reports" : "review")}>
              {admin ? "Open reports" : "Review applicants"}
              <ArrowRight size={15} />
            </a>
          </div>
          {busy ? (
            <p className="role-loading" role="status">
              Loading {admin ? "reports" : "applicants"}…
            </p>
          ) : failed.includes(admin ? "reports" : "applicants") ? (
            retry(admin ? "reports" : "applicants")
          ) : admin ? (
            reports?.items.length ? (
              reports.items.map((report) => (
                <a
                  className="role-record role-report-record"
                  href={href("reports")}
                  key={report.id}
                >
                  <span className="role-record-symbol">
                    <ThinkIcon name="reports" size={24} />
                  </span>
                  <div>
                    <strong>{report.reason}</strong>
                    <span>{manila(report.created_at)}</span>
                  </div>
                  <ArrowRight size={16} />
                </a>
              ))
            ) : (
              <div className="role-quiet-empty">
                <ThinkIcon name="reports" size={36} />
                <h3>No unresolved reports</h3>
                <p>
                  Reported resources will appear here when they need your
                  attention.
                </p>
              </div>
            )
          ) : applications?.items.length ? (
            applications.items.map((application) => (
              <a
                className="role-record role-applicant-record"
                key={application.id}
                href={href("review", application.id)}
              >
                <span className="role-person-initial" aria-hidden="true">
                  {application.student_name.slice(0, 1)}
                </span>
                <div>
                  <strong>{application.student_name}</strong>
                  <span>{application.listing_title}</span>
                  <small>{manila(application.created_at)}</small>
                  <StatusBadge status={application.status} />
                </div>
                <ArrowRight size={16} />
              </a>
            ))
          ) : (
            <div className="role-quiet-empty">
              <ThinkIcon name="applicants" size={36} />
              <h3>No applications to review</h3>
              <p>
                Once a listing is published, students can apply and their
                submissions will appear here.
              </p>
            </div>
          )}
        </section>
      </div>
      <footer className="role-home-footer">
        <ThinkIcon name={admin ? "audit" : "verification"} size={20} />
        <p>
          {admin
            ? "Every verification and moderation decision has a recorded history."
            : "Application documents are shared only with your company and the applicant."}
        </p>
        <a href={href(admin ? "audit" : "profile")}>
          {admin ? "Audit history" : "Company profile"}
          <ArrowRight size={14} />
        </a>
      </footer>
    </div>
  );
}
