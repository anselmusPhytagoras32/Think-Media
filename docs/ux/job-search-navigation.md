# Job search and navigation

FR01–05/08; W01/W03/W04/W06; NFR03/05/09/10.

The owner requested familiar job-platform browsing, seamless preparation, removal
of the desktop topbar, and a sidebar that expands near the cursor with an
optional lock. This refinement preserves ThinkMedia's purple illustrated identity.
The keyword/filter/result pattern draws on [Upwork's job-search guidance](https://support.upwork.com/hc/en-us/articles/211063078-How-to-search-for-jobs-on-Upwork).

## Behavior

- Desktop starts with an 84px rail. Mouse entry or keyboard focus expands it to
  238px over the workspace; the content does not move during automatic expansion.
  Moving both pointer and keyboard focus out collapses it.
- The sidebar contains collapse/expand and lock/unlock buttons. Choosing a width
  manually locks it. Unlock restores automatic expansion. Lock is exposed through
  `aria-pressed`, width through `aria-expanded`, and native titles explain both.
- `thinkmedia.sidebar.v2` stores only auto/expanded/collapsed. Old width preferences
  do not imply consent to lock. Denied storage leaves controls usable in memory.
- Mobile has a menu/brand header, full drawer and bottom task navigation. Drawer
  focus containment, Escape, opener focus restoration and background scroll lock
  remain intact. Keyboard access does not depend on hover.
- Keyword search precedes results. Location/type/skill controls are grouped at
  the left on wide screens and behind a named disclosure on narrow screens.
  Native form association submits them together. Applied filters stay in the URL
  through detail, Back and reload. Clear filters resets the search.
- All opportunities is the initial view. For you loads actual recommendations
  separately, with honest outage/empty states and a Browse all opportunities
  recovery action. Detail/back navigation preserves the selected view.
- Result rows show actual company, title, type, location, description, skills and
  Manila publication date. Verified company reflects the API's eligibility rule;
  it does not claim partnership or endorse a hiring outcome.
- The preparation panel links to profile and own applications, describes PDF
  requirements and reflects the actual presence of course/skills. It invents no
  completion percentage. Student profile save exposes Continue to opportunities.
- The fictional-data notice remains accessible below page content. Company,
  private-file and application-decision APIs are unchanged.

## Verification

- Full Chrome browser pass: 31 tests passed, including shared role workflows,
  private PDF handling, publication, registration, onboarding and mobile navigation.
- Targeted pass: eight tests passed for sidebar preference/focus/hover/lock,
  denied storage, registration/profile/verification and opportunity filtering.
  The opportunity test includes real combined API filters, suggestion outage,
  detail/back/reload/clear and desktop/mobile axe scans.
  After lifting the view state, the opportunity regression passed again with an
  additional assertion that returning from a suggestion restores For you.
- Native rendered review: 1920, 1440, 1024, 768 and 360px with real local synthetic
  listing records; no horizontal overflow, first result titles visible within
  the first viewport. Screenshots are local `.local/opportunities-*.png` artifacts.
- Production TypeScript/Vite build passed; Impeccable detector returned no findings.

These are implementation checks using fictional records, not user research or a
claim that the new layout has measured usability outcomes.

## Mobile More page

The bottom More destination now navigates to `#/more`, a full page with profile,
role-specific workspace destinations, Getting started and Sign out. It exposes
`aria-current=page`, supports reload/browser Back, and enters at the top even
from a scrolled Home. Main receives focus without moving the page under the
mobile header. The header menu still provides the existing drawer.

Twelve targeted browser checks have passing evidence across the initial run and
two corrected reruns, covering navigation, role filtering, profile, sign-out,
introduction replay and the desktop/sidebar flows. The More route passed axe at
360px; its rendered screenshot is `.impeccable/review/more-360.png`.
TypeScript/Vite build passed after the final focus correction.
