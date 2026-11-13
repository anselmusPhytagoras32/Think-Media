// FR04/06/W03; NFR05/09: identity comes from the actual saved company name.
type CompanyIdentity = { companyId: string; companyName: string };
export function CompanyLogo({
  companyId,
  companyName,
  className = "",
}: CompanyIdentity & { className?: string }) {
  const classes = `company-logo ${className}`;
  const initials = companyName
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => Array.from(word)[0])
    .join("")
    .toUpperCase();
  return (
    <span
      className={`${classes} company-logo-fallback`}
      data-company-id={companyId}
      aria-hidden="true"
    >
      {initials || "—"}
    </span>
  );
}
export function CompanyCover({ companyId, companyName }: CompanyIdentity) {
  return (
    <div className="company-cover" data-company-id={companyId}>
      <CompanyLogo companyId={companyId} companyName={companyName} />
      <div>
        <strong>{companyName}</strong>
      </div>
    </div>
  );
}
