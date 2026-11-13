# Administration and company workspaces — November 14, 2026

## Direction

Administration, company home and verification share the student workspace's
Manrope/DM Sans typography, rose emphasis, rounded surfaces, pastel task
destinations and purple custom marks. The role screens prioritize actual work:
review companies/resources/reports, or manage listings/applicants/profile.
The earlier review-tools sidebar and role-explanation footer no longer appear
on these homes. No generic performance metrics or invented activity replace them.

`workspace-art.tsx` supplies original decorative SVG compositions around the
existing ThinkMedia marks. `brand.tsx` adds organization, listing-board and
applicant marks to the same stroke/fill system. Their colors come from the
student palette; their labels remain native HTML. There are no new raster assets.

## Dashboard behavior

Task destinations use actual API totals when available and neutral descriptions
while loading or unavailable. Recent records retain their real IDs, titles,
statuses and ownership. A failed read has its own retry state and is not shown as
an empty queue. Lists are bounded; the linked workspaces retain pagination.

Pending/rejected companies see an explicit verification notice and profile
action. Only verified companies receive the direct first-listing action.
`#/opportunities?new=1` opens the existing editor for an eligible company; reload
preserves that intent and Cancel removes it. Successful saving navigates to the
actual listing. Server-side authorization remains unchanged.

## Verification behavior

Desktop places the bounded, independently scrollable organization queue beside
the review surface. Selecting a record opens its organization/contact details,
status, decision and required reason. The selected ID is preserved in the URL
and can be reopened on reload. Past decisions remain inspectable without a new
decision form.

At narrow workspace widths, selection opens a focused detail view instead of
placing the form beneath the entire queue. Back returns to the queue and restores
focus. The reason and decision are controlled fields retained after validation
failure. Inline errors are associated with their inputs. Version conflicts block
resubmission until company details are refreshed; a company already verified in
another tab then appears as a recorded state. Confirmation still submits the
expected version to the existing audited endpoint. Guidance uses a compact,
accessible launcher on review/create screens to reduce interference with forms.

On phones the destinations stay in a compact three-column layout, records and
work sections stack, and review fields remain large enough for touch. The real
verification decision is never replaced by an illustrated or simulated outcome.

## Requirements and evidence

FR02/06/07/11; W05/W08; NFR02/04/05/09/10. All business rules and API contracts
remain server-controlled. No schema, provider, credential or production-data
change belongs to this refinement.

Four new browser checks exercise real isolated accounts, mobile/desktop layouts,
deep-link/reload, verification, first-listing entry/cancel, unverified denial,
field-error preservation, retry and an actual concurrent verification conflict.
They passed in 19.6 seconds before the full regression run. The checks include
axe scans with WCAG 2/2.1 A/AA tags, adding label-in-name coverage. This caught
and fixed the admin bottom navigation's visible Verify/accessibility-name mismatch.
Production TypeScript/Vite compilation passed; Impeccable's detector returned `[]`.
The final full browser suite passed all 46 tests in 146.084 seconds, with zero
skipped, unexpected or flaky results. Machine evidence is
`.local/qa-role-workspaces.json`. Existing student discovery, guidance, company
application review and administration flows passed alongside the four new checks.

Screenshots under `.impeccable/review/`: `admin-workspace-new-{1440,768,360}.png`,
`company-workspace-new-{1440,768,360}.png`, `verification-new-1440.png` and
`verification-new-360.png`. These use fictional records in the isolated browser
database, with external AI disabled. Chrome viewport emulation establishes the
tested layout/input behavior, not physical-device or human screen-reader testing.

Intent and Impeccable guided consistency and layout; Articulate guided action
labels and recovery copy. Verification evidence concerns the implemented flows,
not a claim of measured user satisfaction or a human usability study.
