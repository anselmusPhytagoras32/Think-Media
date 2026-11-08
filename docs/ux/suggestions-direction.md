# Suggestions

FR08–09; W06; NFR03/05/09.

## Purpose

Help a student choose a relevant opportunity or preparation resource, understand
why it appears, and optionally share a relevance rating. Keep the published
eligibility, profile/general/hybrid modes and application decisions unchanged.

## Design constraints

- Recommendations should be easy to scan, with company identity for listings
  and semantically matched artwork for resources.
- Give opportunities and learning clear destinations. Profile guidance belongs
  near the recommendations without displacing them with a large warning panel.
- Use the actual explanation supplied for each recommendation. Do not fabricate
  match percentages, completion scores or guarantees of placement.
- Treat relevance rating as an optional secondary action. Rendering a card,
  opening its rating controls, or choosing a number must not submit feedback.
  Only Share rating records the selected numeric value.
- Keep explicit save/error messages adjacent to the rating control. Clear stale
  success text when the selected value changes.
- A failed refresh must not present stale recommendations/counts as newly fetched
  results. Provide a retry and direct browsing destinations.
- Preserve keyboard focus, accessible labels, actual detail destinations,
  mobile navigation and readable layouts from 360px upward.

## Acceptance evidence

The real profile/rating browser test checks that feedback requests remain zero
until Share rating is pressed, that a numeric rating is saved through the API,
and that a recommended published resource opens through its real destination.
The layout regression covers the additional navigation and state behavior.
All three browser checks passed: the real profile/rating flow, the new responsive
state regression and the role-workspace accessibility scan (29.7 seconds).
TypeScript/Vite production build passed with 1607 modules. The design detector
returned no findings.

Native Chrome render review at 1440, 768 and 360px confirmed no horizontal
overflow and bounded resource artwork. On the same fictional local account,
the first suggestion moved from y438 to y295 at 1440px and from y626 to y371
at 360px. These are layout observations, not user-research outcomes.
Screenshots are `.local/suggestions-*.png` and
`.local/suggestions-learning-*.png`.
