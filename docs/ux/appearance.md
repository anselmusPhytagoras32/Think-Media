# Appearance

NFR03/05/09. A light/dark toggle is available at sign-in, in the desktop sidebar
and under Account on the mobile More page. Light remains the default. The choice
is a nonpersonal preference in browser-local storage (`thinkmedia.theme.v1`),
applied before rendering and synchronized across tabs. If storage is blocked,
the current page can still switch themes; persistence is unavailable.

The dark palette uses purple-black canvas, raised purple surfaces, pale text and
the existing rose/teal accents. Existing light colors remain exact variable
fallbacks. Illustrations retain their original colors. Native controls follow
the selected color scheme, and focus styling remains visible.

No backend setting, account field, provider call or database migration is involved.
Browser checks cover persistence, return to light mode, blocked storage, mobile
containment, student pages, chat, instructor authoring, company listings and
administrator verification. Automated accessibility checks supplement visual
inspection; they do not constitute human assistive-technology testing.
