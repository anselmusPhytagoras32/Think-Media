// FR04/06/W03; NFR05/09: one mock identity per actual company, shared on home/results/details.
type CompanyIdentity = { companyId: string; companyName: string };
function brand(companyName: string) {
  const normalized = companyName
    .toLowerCase()
    .replace(/\(synthetic\)/g, "")
    .trim();
  return normalized === "demo practice studio"
    ? {
        key: "demo-practice-studio",
        src: "/company-logos/demo-practice-studio.svg",
        name: "Demo Practice Studio",
      }
    : null;
}
export function CompanyLogo({
  companyId,
  companyName,
  className = "",
}: CompanyIdentity & { className?: string }) {
  const identity = brand(companyName);
  const classes = `company-logo ${className}`;
  if (identity)
    return (
      <img
        className={classes}
        src={identity.src}
        alt=""
        width="80"
        height="80"
        data-company-id={companyId}
        data-logo-key={identity.key}
        decoding="async"
      />
    );
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
  const identity = brand(companyName);
  return (
    <div className="company-cover" data-company-id={companyId}>
      <CompanyLogo companyId={companyId} companyName={companyName} />
      <div>
        <strong>{identity?.name || companyName}</strong>
        {identity && <span>Mock company</span>}
      </div>
    </div>
  );
}
