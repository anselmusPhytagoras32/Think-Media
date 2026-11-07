# Responsive navigation and welcoming sign-in

## Implemented scope

The user approved the existing student visual style, requested a more intuitive responsive layout and collapsible sidebar, then supplied an illustrated login reference. The palette, four existing task graphics, actual API data and backend workflows are preserved. Current direction: [layout/sign-in contract](thinkmedia-layout-signin-direction.md).

- Desktop navigation toggles between a full rail and compact icons. Accessible names remain, and hover/keyboard focus displays labels. The toggle remains in the sticky topbar. A nonpersonal `thinkmedia.sidebar.v1` preference records expanded/collapsed locally and fails safely when storage is blocked.
- Tablet defaults to compact navigation unless the user explicitly chooses otherwise. Mobile retains a full drawer and bottom task bar. The drawer locks page scrolling, contains keyboard focus, closes with Escape and recovers scroll/focus when resized into desktop navigation.
- Discovery adapts to actual workspace width using container queries. On wide screens, application/guidance support starts beside the heading/search/categories, using the earlier empty upper-right area. Narrow screens retain the mobile discovery order and swipeable opportunity cards.
- Sign-in uses an original full-bleed campus study scene on the left and a clear native form on the right. A compact illustrated header serves mobile. The real form retains role registration, email/password validation, password visibility, privacy information, onboarding replay and existing FastAPI authentication.
- The fifth original illustration is a 1024×1365 WebP, 175,106 bytes, with exact prompt provenance. It depicts no real participant. Native text overlays a darkened image region for legibility; controls and branding remain HTML/SVG. No unsupported sign-in providers or recovery actions were invented.

## Executed checks

The scoped sidebar tests passed: keyboard collapse/expand, route navigation, reload persistence, blocked storage, account controls, desktop/tablet/mobile adaptation, no horizontal overflow, drawer scroll lock and resize focus recovery. The illustrated sign-in tests passed at desktop/tablet/phone widths with selected axe scans, registration-mode/role controls, password visibility and real student sign-in/no-admin access. These are executable checks against the isolated local browser API, not mocked application data.

The sidebar phase passed all19 browser/API tests. After sign-in integration, five focused layout/sign-in tests passed40.9s. The integration production build passed59.66s with1,599 modules; JavaScript335.46kB/gzip97.11kB. The final combined suite passed **21 browser/API tests**, approximately1.4minutes, after the final mobile crop and resize-focus updates.

Captured evidence under `.impeccable/review/`: `layout-1920.png`, `layout-1440.png`, `layout-1024.png`, `layout-768.png`, `layout-360.png`, `sidebar-collapsed-1440.png`, `sidebar-tooltip-1440.png`, and `signin-scene-{1440,768,390,360}.png`.

The initial shell regression caught an account-link accessible-name mismatch. Expanded links now use their visible native text, while the collapsed icon control retains an explicit name. A render pass aligned breadcrumbs with the toggle and kept desktop tooltip labels above the sticky header. The mobile image crop keeps the illustrated face clear of the brand badge.

## Boundaries

FR01–11 and NFR03/05/09/10 guide the UI changes. No backend application logic, schema, role authorization, private attachment handling, user/demo records or production resources changed. User-facing API8000/database and isolated browser API8001/database remain separate. The external runtime AI setting is unchanged. No deployment, push, real messages, production changes or destructive cleanup occurred.

Automated axe and keyboard checks cover selected states and do not constitute full accessibility certification. No measured participant usability improvement is claimed. Existing genuine research evaluations remain pending data.

Final mechanical checks: Impeccable detector exit0 with `[]` (`layout-signin-detector.json`); five raster assets have prompt provenance with zero missing; Prettier and `git diff --check` passed. The design record was synchronized with actual shell/auth tokens and the fifth artwork.

Final review identified one compact-sidebar tooltip recovery issue. Labels now remain visible when hovered and dismiss with Escape while retaining anchor focus. All five focused layout/sign-in browser tests passed again in 41.2s after the final pointer-gap correction (`frontend/test-results/.last-run.json`: passed, no failures). The production build after Escape handling passed in 33.93s. After the pointer-gap correction, the final build passed in 1m 6s with 1,599 modules; JavaScript335.66kB/gzip97.14kB and CSS72.70kB/gzip17.51kB. The user-facing API8000 was restarted using its existing local launcher; API health and UI5173 returned200. No test data was moved into the user database.

Independent final review: **ship**. The original tooltip finding is resolved through live 12-step pointer travel onto the label, Escape dismissal, preserved Learning focus and Enter navigation. The regression now uses stepped mouse movement rather than a direct hover jump.


## Full-scene visual refinement

Following the supplied reference, the sign-in composition now uses a single full-viewport botanical campus illustration with foliage framing every edge, including behind the glassy sign-in card. The student and desk anchor the left side, while the lower-detail garden on the right keeps the real form legible. On phones the art remains the backdrop, with a compact opaque-enough form card and no separate cropped hero strip. The 1800×1013 WebP background is 227,300 bytes; the previous student-scene asset remains available for existing uses. Desktop, 390px and 360px screenshots are in `.impeccable/review/signin-fullbg-{desktop,mobile,small}.png`. The latest production build is running.
