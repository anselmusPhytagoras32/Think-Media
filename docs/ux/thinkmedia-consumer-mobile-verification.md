# Consumer mobile discovery and local account

## Implemented

The user's job-app reference now governs the student home’s actual structure: discovery heading, working search/filter control, three illustrated destinations, recent opportunity cards, learning previews and the student's application tracker. At phone widths, opportunity cards use native horizontal scrolling with snapping and a visible next-card edge. At desktop widths, work uses columns. The palette and full-color onboarding backgrounds remain.

Three additional original transparent illustrations join the original welcome character: a learning still life, a student exploring opportunities, and application stationery. Four WebP assets total 486,074 bytes; each has an adjacent exact generation-prompt record. Artwork is decorative and carries no real participant, employer or placement claim. Onboarding changes artwork by step; learning and listings use their own subjects.

Student home loads real `/listings`, `/content` and `/applications/me` responses. Search/category filters become actual API parameters; keyword/type/location/skill state survives URLs, reload, detail/back and clear. Published-only/verified-company and ownership controls stay server-side. No endpoint data is replaced by frontend fixtures.

## Local consumer setup

The user requested a consumer account. Alex Student is provisioned with the student role at `student@example.test`; its local password is provided directly to the user and kept in the private runtime environment. Login and `/auth/me` return 200; administrator reads return 403. The user API at `http://127.0.0.1:8000` serves three clearly labeled synthetic opportunities and three published guides with quizzes, with empty initial application history. These records are local demonstrations, not vacancies, partners or research observations.

PostgreSQL runs on loopback port 55432 with persistent Linux data under `~/.local/share/thinkmedia/pgdata`, outside `/tmp`. The separately provisioned administrator remains separate; users cannot self-register admin. The API database role is not superuser and cannot create databases. The ignored `.local/start-backend.sh` restarts this local setup; [local demo instructions](../LOCAL_DEMO.md) describe its private configuration and backup.

The previous temporary database was unavailable after the environment restart. Its data was not silently replaced as if recovered. The new local seed is idempotent and refuses unknown account ownership; repeated runs preserve profile edits, applications and listing/content state. A private logical backup and fresh restore check verified schema and all 19 tables.

## Verification

- Frontend production build passed after implementation. Final production build passed34.15s; the bundle is332.50kB JavaScript / gzip96.29kB.
- Backend `pytest -q --tb=short`: **114 passed**,70.87s with explicit disabled-provider fixtures and an isolated authenticated PostgreSQL test role.
- Full browser/API suite: **16 passed**, approximately 1.2 minutes. This includes student login/no-admin access, actual search/category filters, reload/detail/back/clear, graphics loading, selected axe states, 360px/390px/768px/1440px layout checks, company/application/learning/guidance flows and keyboard navigation.
- Browser regressions run against separate `thinkmedia_browser_local` through API8001 and frontend5174, keeping test records out of the user's demo feed on8000/5173. `thinkmedia_backend_test` is a third isolated database for backend pytest.
- Actual user-API browser capture confirmed student role, admin403, listings3/resources3 and zero runtime errors. Captures: `.impeccable/review/consumer-live-mobile.png` and `consumer-live-desktop.png`; viewport matrix: `consumer-360.png`, `consumer-390.png`, `consumer-768.png`, `consumer-1440.png`.
- One Impeccable detector pass returned exit0 and `[]`, saved as `.impeccable/review/consumer-detector.json`.
- Asset provenance scan: four rasters, zero missing. Prettier and `git diff --check` passed.

The initial backend recheck exposed test-configuration problems: the local retrieval-mode environment affected tests expecting a disabled provider, and migration tests needed an isolated role with database-creation permission. The migration test also used SQLAlchemy’s redacted URL string instead of a usable connection URL. Test defaults and URL construction were corrected, and a separate restricted test role/database was created without changing user API privileges. Backend application logic and migrations were preserved.

## Scope and limits

FR01–05/08/10–11 and relevant NFR02–07/09–10 guide the changes. No production deployment, push, real messages, external AI call, destructive user-data cleanup or fabricated research metrics occurred. Automated accessibility scans are selected-state evidence, not certification or measured participant usability improvement. Daily backup scheduling and genuine research evaluation remain separate work.

## Independent finishing corrections

The fresh reviewer confirmed that the new mobile composition follows the supplied reference family, then identified two narrow defects: opportunity-card focus was clipped by its rounded parent, and the search placeholder implied skill matching beyond keyword-search behavior. The link now inherits card rounding and paints its purple focus ring inside the card; the hint says “Role, title or keyword.” Four focused consumer/onboarding tests passed21.7s after correction, including keyboard focus/Enter navigation and search reload/detail/back/clear. Focus renders were captured at360px and1440px. No second detector pass was run.

The independent reviewer scored both listed corrections resolved and returned `disposition: ship` for this reviewed consumer/mobile scope. The final source build and formatting checks passed. Actual user-database captures still confirm student role, admin403, exactly three demo listings/three guides and zero browser runtime errors.
