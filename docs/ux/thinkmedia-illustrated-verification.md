# Illustrated workspace and first-use introduction

## Delivered

The user's job-app references and supplied palette replace the earlier green identity. The current surface contract is [illustrated direction](thinkmedia-illustrated-direction.md); durable tokens and component guidance are in [DESIGN.md](../../DESIGN.md) and `.impeccable/design.json`.

- Original custom book/seed brand mark and eleven duotone navigation/content icons.
- Original transparent dimensional student/laptop artwork; production WebP is 142,880 bytes at 960×877. Exact generation prompt is retained in `frontend/public/illustrations/thinkmedia-welcome.webp.json` and `.impeccable/assets/thinkmedia-welcome.prompt.txt`. Artwork is decorative, not a real participant or employer claim.
- Purple text/actions, white rounded work surfaces, turquoise/rose/peach/blush/lavender task accents, and readable lifecycle statuses using the supplied palette and contrast-adjusted tints.
- Illustrated home and sign-in, matching opportunity/learning emblems, refreshed forms, mobile navigation, company and administrator screens. Existing real queues and API integration are retained.
- Three optional first-use steps: Prepare, Explore, Apply. Next, Back, numbered progress controls, Skip and Sign in remain available. Completing can open the actual registration form. Signed-in replay returns to the workspace without ending the session.
- Completion is a browser-local, versioned `thinkmedia.welcome.v1=seen` marker only. No account, credential, application or profile data goes into localStorage. Storage restrictions fall back to in-memory dismissal. Replay is available from sign-in and the account navigation.

## SRS trace

| Change | Requirements |
| --- | --- |
| Welcome, role entry and sign-in | User-requested introduction; FR01–02, W01, NFR03/05/09 |
| Real task home, discovery, listing/application UI | FR03–07, W02–W05, NFR04/05/09 |
| Suggestions, guidance, admin styling | FR08–11, W06–W08; preserve source citations, uncertainty and server permissions |
| Custom graphics, typography, responsive and keyboard states | NFR05/09/10, English and Asia/Manila |

## Executed verification

| Command/check | Actual result |
| --- | --- |
| `npm run build --prefix frontend` | Passed; TypeScript + Vite, 1,593 modules, final build 33.19s; app JS 322.82 kB / gzip 94.24 kB |
| `LD_LIBRARY_PATH=/tmp/thinkmedia-browser-runtime/usr/lib/x86_64-linux-gnu npm test --prefix frontend` | **15 passed**, 57.4s; actual FastAPI and disposable local PostgreSQL |
| Same command with `-- marketplace.spec.ts workspace.spec.ts` | **4 passed**, 12.6s after the final mobile illustration and screenshot/replay regression updates |
| Impeccable `detect frontend/src frontend/index.html --json` | Exit 0; `[]` saved in `.impeccable/review/illustrated-detector.json`; one pass |
| Impeccable `embed-prompt --scan frontend/public/illustrations` | One raster, zero missing provenance |
| Prettier check of source/tests/index | Passed |
| Additional auth/admin browser capture | No browser runtime errors |

The full suite includes real registration/profile/verification, company publication and applicant review, private PDF access, invalid-file rejection, confirmation edit/collapse, learning save/react/quiz/moderation, actual suggestions, guidance and provider recovery, route persistence/retry and automated axe scans across selected role states. The three new onboarding tests cover step keyboard focus and Back, all three phone-width axe states, dismissal/reload, replay, real registration entry and blocked localStorage. A focused signed-in replay assertion also confirms the authenticated session remains valid.

## Visual evidence

Files in `.impeccable/review/` inspected at 1440px, 768px and 360px:

- `illustrated-onboarding-desktop.png`, `illustrated-onboarding-mobile.png`
- `illustrated-auth-desktop.png`, `illustrated-auth-mobile.png`
- `ux-home-desktop.png`, `ux-home-768.png`, `ux-home-360.png`, `ux-home-active-360.png`
- `illustrated-admin-desktop.png`, `desktop-listing.png`
- `ux-application-review-360.png`, `mobile-application.png`
- `mobile-learning.png`, `mobile-assistant.png`, `mobile-suggestions.png`

The mobile home artwork was contained within its panel after inspection. The application-detail capture now waits for actual loaded data. Full-page captures of a fixed mobile task bar show that bar at the viewport boundary within the longer document; this is capture behavior, not a second inline bar.

## Boundaries

No backend logic, schema, migrations, authorization or attachment handling changed. Real PostgreSQL data drives the app; synthetic records belong to the disposable test database. External runtime AI stays disabled by user choice; the generated illustration contains no private application data. No deployment, push, production mutation, messages or destructive cleanup occurred.

Automated accessibility checks cover selected states and keyboard tests, not certification. No participant usability improvement, research metrics, actual employer ratings or fictitious salary/count data is claimed. First-use dismissal follows this browser, not the account across devices; that is a documented local-MVP assumption.

## Independent finish review

Disposition: **ship**, scoped to the supplied illustrated UI captures and source for this local MVP. A fresh native Codex reviewer inspected the visual reference, palette, current direction and rendered role/onboarding screens; no material fixes were requested. The reviewer specifically retained the optional introduction, skip/replay, real statuses/history, submission review and privacy boundaries. This is design review evidence, not deployment approval or accessibility certification. The documentation pass updated DESIGN.md, its schema-v2 sidecar and PRODUCT.md to the actual rendered system.

## Full-color onboarding background

At the user’s request, each introduction step now fills the whole viewport with its color, including the area around and below the illustration: blush, turquoise and lavender. Secondary copy was darkened for contrast. The three existing onboarding/browser/axe checks passed again (7.9s); the refreshed 360px capture was inspected.
