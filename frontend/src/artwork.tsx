// FR03–05, NFR05/09: original, decorative artwork; no employer or outcome claims.
export type ArtworkKind =
  "welcome" | "learning" | "opportunities" | "applications";
export function Artwork({
  kind,
  className = "",
  priority = false,
}: {
  kind: ArtworkKind;
  className?: string;
  priority?: boolean;
}) {
  return (
    <img
      className={`product-artwork ${className}`}
      src={`/illustrations/thinkmedia-${kind}.webp`}
      alt=""
      width="960"
      height="960"
      loading={priority ? "eager" : "lazy"}
      fetchPriority={priority ? "high" : "auto"}
      decoding="async"
    />
  );
}
