# Product
<!-- impeccable:product-schema 1 -->

## Platform
web

## Stack
React, TypeScript and Vite client; existing Python FastAPI modular monolith; PostgreSQL. Preserve the backend and its cookie/CSRF protocol.

## Users
College students preparing for OJT use phones and desktops to find placements, submit requirements and track decisions. Companies manage their own listings and applicants. Instructors browse public opportunities and approved resources. Separately provisioned administrators verify companies and moderate content.

## Product Purpose
Connect preparation, opportunity discovery and accountable application review in one workspace. Success means a verified company can publish, a student can apply once, and both can track an authorized decision.

## Operating Context
English interface, Asia/Manila dates, responsive down to 360px. Authority: root Requirements Software Engineering.docx, latest cumulative PD7 sections 1–7; the complete extract in .ai-team/spec/ remains supporting reference. The delivery target is a local MVP, as clarified by the user. Cloud hosting is outside this work.

## Capabilities and Constraints
FR01–12 and NFR01–11 govern implementation. Only verified companies publish. Private applications and attachments stay out of AI prompts. Recommendations are suggestions. No self-service administrator role, scraping, payments, live messaging, deployment or production changes.

## Brand Commitments
ThinkMedia. Plain, professional English; descriptive controls and visible errors. The user supplied job-app screenshots as the visual reference and explicitly requested a replacement identity with soft rounded cards, welcoming original graphics/custom icons and a first-use introduction. The pinned palette is #718444, #72C7D0, #E0B0A4, #D7A3B7, #D8789E, #AE6873, #ED4D6E, #8A77A7 and #402C75. Deep purple anchors readable actions; lighter colors support surfaces and artwork. These references supersede the earlier green implementation assumption.

## Evidence on Hand
The SRS, backend implementation, executable tests and user-provided visual references. Five original generated illustrations cover welcome, opportunities, learning, applications and the full-scene sign-in welcome. Each is decoration, with its exact prompt stored beside the asset; it is not a real participant image. No confirmed pilot dataset, partner claims, testimonials or measured evaluation results.

## Product Principles
- Complete the application workflow before adding intelligence.
- Explain status, consequences and recovery at the point of action.
- Keep private information accessible only to authorized parties.
- Report missing data and unavailable services honestly.

## Accessibility & Inclusion
Labeled controls, keyboard navigation, visible focus, live status announcements, sufficient contrast, reduced motion and 360px layouts.

## Assumptions and open decisions
Implementation assumption: first-use orientation is optional and browser-local, with three introduction steps and skip/replay. The version marker `thinkmedia.welcome.v1=seen` and nonpersonal navigation preference `thinkmedia.sidebar.v1=expanded|collapsed` are saved in localStorage; no profile data, credentials, application documents or session values belong there. Storage denial falls back to in-memory welcome completion and sidebar preference so entry and navigation still work; another browser or cleared storage may show the introduction again. Role setup and authorization remain server-controlled. Privacy/retention policy, verification evidence, hosting, runtime LLM provider and budgets require decisions before pilot. No invented listings or learning resources will appear as real records.

## Runtime guidance decision
User chose to keep external AI disabled and use approved-resource lookup for now. The local development API explicitly enables retrieval; the code default remains disabled. Research effectiveness is not asserted without genuine supplied datasets.

## Workspace refinement
Existing Intent and Impeccable skills guide the local MVP. The approved illustrated direction is recorded in docs/ux/thinkmedia-illustrated-direction.md, with the responsive-shell and welcoming sign-in refinement in docs/ux/thinkmedia-layout-signin-direction.md; DESIGN.md captures its implemented visual system. The student account now opens a consumer discovery home with distinct illustrated category destinations, recent published opportunities, approved learning previews and the student’s own application pocket. Search and type/skill/location filters use real API parameters retained in the URL through reload and detail/back navigation. Preserve real role work, stable URLs, clear application confirmation, mobile task navigation and direct feed actions within the illustrated identity; company, instructor and administrator workflows retain their role-specific structure. The sidebar supports expanded and compact desktop modes with accessible destination names and labels; mobile retains the full drawer and bottom navigation. Discovery adapts to available workspace width, including the space recovered by collapsing the sidebar. Sign-in pairs an original campus illustration with the existing real account form, registration roles and password visibility; phones retain a compact illustrated header. Workflow choices follow the SRS; no participant research findings are asserted.
