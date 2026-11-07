// FR05–07/11: status is explicit text, with supplemental semantic color.
export function StatusBadge({ status }: { status: string }) {
  const labels: Record<string, string> = {
    submitted: "Submitted",
    under_review: "Under review",
    accepted: "Accepted",
    rejected: "Rejected",
    draft: "Draft",
    published: "Published",
    closed: "Closed",
    pending: "Pending verification",
    verified: "Verified",
  };
  return (
    <span className={`status-badge status-${status}`}>
      <span className="status-dot" aria-hidden="true" />
      {labels[status] || status.replaceAll("_", " ")}
    </span>
  );
}
