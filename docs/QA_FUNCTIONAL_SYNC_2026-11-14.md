# Functional data and Guidance correction — November 14, 2026

The reported problem was stale data across locally created accounts and weak
Guidance answers. This work corrects existing Phase 1–4 behavior within the
Phase 5 QA scope; it does not invent activity to populate a presentation.

## What changed

FR01/02/04–11, NFR03/05/06/11: visible role workspaces refresh on focus, after
successful relevant writes and every five seconds while visible. A shared
browser signal contains topic names only. Each workspace still fetches its
authorized API records. Application review, listing editors, quizzes and
other active forms keep their drafts. Background refresh preserves the screen
instead of repeatedly showing an initial loading state. Failed home requests
show unavailability rather than manufactured zero counts.

The account session also refreshes without remounting the workspace, so company
verification reaches an already signed-in company. Company covers display the
actual stored organization name, including any synthetic labels already present
in the data. Company dashboards show their own listings/applicants; student
discovery shows eligible public listings across verified companies.

A new company belongs in the administrator's pending queue. Its account alone
does not produce a student opportunity. The company must be verified, create
a real listing and confirm publication. Draft and closed listings remain
excluded from public discovery. Separate browser profiles or isolated contexts
are needed when demonstrating different roles because tabs share session cookies.

FR03/10/11, NFR03/06/11: Guidance now removes common search words, normalizes
topic variants, ranks matching published resources and extracts relevant
passages instead of taking only the newest records and their first 800
characters. Three preceding user questions can resolve follow-ups; an unrelated
new topic does not inherit old sources. Requests for examples prioritize actual
illustrations. Up to three source excerpts of 1600 characters each remain
bounded by the provider's total request-byte limit. Citations must refer to
the retrieved published resources.

Five practical OJT guides and two instructions for implemented platform
workflows were published through the existing local administrator API. They
are actual readable learning resources used by retrieval, with public source
provenance for career guidance. No accounts, listings, applications, ratings or
research participants were added to presentation data. Existing records were
preserved. Rerunning the publication command reported all seven unchanged.

## Verification and reproduction

The initial regression checks reproduced two stale-role failures and three
retrieval failures before their fixes. Cross-role browser verification now
covers registration → administrator queue → verification → company access →
publication → student discovery → application → company review → student
acceptance, without reloading. It also checks company-name changes and an
unsaved listing surviving an account refresh. These writes use only isolated
browser API8001 and its disposable PostgreSQL database.

Commands from the repository root, using the existing local runtime:

```powershell
wsl -d Ubuntu -- bash scripts/verify-local.sh
cd frontend
npm.cmd run build
$env:PLAYWRIGHT_API_TARGET='http://127.0.0.1:8001'
$env:PLAYWRIGHT_CHANNEL='chrome'
npm.cmd test
```

The browser suite includes authorization failures, private attachment handling,
invalid file recovery, listing/application workflows, publication, unavailable
Guidance, retry, sources, 360px layouts, keyboard focus and automated axe scans.
The existing negative backend tests cover ownership, unverified publishing,
duplicate/closed applications, unauthorized downloads and transactional rollback.

The read-only presentation audit compared administrator company records, public
student listings, published learning records and the operator company's own
listings. It found matching stored IDs, names and eligibility. The presentation
company has no owned listings; another company's published listings are correctly
visible to students. Three pre-existing public listings were preserved.

Live Gemini checks used only generic non-private questions: STAR interview
preparation, a concrete follow-up example, company verification/publication,
and a résumé without employment experience. All four returned HTTP 200 in
external mode with resolvable citations and topic-specific text. The follow-up
actually used the guide's illustrative class-presentation example. The local
configuration remains `gemini-3.5-flash-lite`, with an explicitly set 20-second
timeout, 1024-token cap and unchanged 25-attempt process budget.

Private local evidence: `.local/cross-role-data-audit.json`,
`.local/guidance-quality-check.json`, `.local/qa-functional-2026-11-14.json`.
These contain engineering checks, not pilot evaluation outcomes. Research
measurements, real CSAT sampling and physical-phone keyboard verification
retain the limitations documented in the existing presentation-readiness report.

Backend verification: **245 passed** in 118.83 seconds. Alembic detected no
new upgrade operations. All **8 evaluation-pipeline tests passed**. The final
frontend production build passed. The final full browser run passed **48 tests**
in 161.57 seconds, with zero unexpected, skipped or flaky tests.
`git diff --check` passed. The frontend5173 proxy returned the same listing IDs
as presentation API8000. Credential-free machine evidence is in
`backend/reports/functional-sync-guidance-local.json`.
