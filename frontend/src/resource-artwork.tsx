// FR03/W02; NFR05/09: topic illustrations follow content semantics across surfaces.
export function resourceArtworkTopic(title: string, tags: string[]) {
  const topic = `${title} ${tags.join(" ")}`.toLowerCase();
  if (/portfolio|react|frontend|front.end|web|design|\bux\b|\bui\b/.test(topic))
    return "web-portfolio";
  if (
    /python|sql|data|coding|\bcode\b|programming|backend|database/.test(topic)
  )
    return "coding-data";
  if (
    /resume|résumé|\bcv\b|application|interview|career|workplace|ojt/.test(
      topic,
    )
  )
    return "application-prep";
  return "general";
}
export function ResourceArtwork({
  title,
  tags,
  className = "",
  priority = false,
}: {
  title: string;
  tags: string[];
  className?: string;
  priority?: boolean;
}) {
  const topic = resourceArtworkTopic(title, tags);
  return (
    <img
      className={`resource-artwork ${className}`}
      data-artwork-topic={topic}
      src={
        topic === "general"
          ? "/illustrations/thinkmedia-learning.webp"
          : `/illustrations/learning-${topic}.webp`
      }
      alt=""
      width="960"
      height={topic === "general" ? 960 : 720}
      loading={priority ? "eager" : "lazy"}
      fetchPriority={priority ? "high" : "auto"}
      decoding="async"
    />
  );
}
