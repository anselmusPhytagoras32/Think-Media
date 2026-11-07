// FR08 / NFR05: explain the actual ranking signal without exposing implementation jargon.
export function suggestionReason(reason: string) {
  if (reason.includes("No shared profile terms"))
    return "Recently published. No close profile match yet.";
  if (reason.includes("Based on shared terms"))
    return "Matches details in your profile.";
  if (reason.includes("optional ratings from users"))
    return "Based on your profile and rating preferences.";
  if (reason.includes("actual popularity"))
    return "Based on recorded activity on this resource.";
  if (reason.includes("No recorded activity"))
    return "Recently published; no activity recorded yet.";
  if (reason.includes("Recent eligible resource"))
    return "Recently published. Add profile details for more relevant suggestions.";
  return reason;
}
