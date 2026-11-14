// FR06/07/11, NFR05/09: decorative 3D task art; destination labels remain native text.
export type WorkspaceArtKind =
  | "verification"
  | "reports"
  | "learning"
  | "listing-board"
  | "applicants"
  | "organization";

export function WorkspaceArt({
  kind,
  className = "",
}: {
  kind: WorkspaceArtKind;
  className?: string;
}) {
  return (
    <img
      className={`workspace-art ${className}`}
      src={`/illustrations/workspace-${kind}.png`}
      alt=""
      width="160"
      height="128"
      loading="lazy"
      decoding="async"
    />
  );
}
