---
name: ThinkMedia
description: A welcoming illustrated OJT workspace with rounded surfaces and clear next actions.
colors:
  deep-purple: "#402c75"
  purple-hover: "#57428b"
  turquoise: "#72c7d0"
  vivid-rose: "#ed4d6e"
  olive: "#718444"
  peach: "#e0b0a4"
  blush: "#d7a3b7"
  pink: "#d8789e"
  dusty-rose: "#ae6873"
  lavender: "#8a77a7"
  ink: "#34244f"
  muted: "#6b607c"
  paper: "#faf8fc"
  white: "#ffffff"
  divider: "#e5deeb"
  panel-border: "#e8e1ee"
  control-border: "#95899f"
  control-surface: "#fffdff"
  active-navigation: "#f0e6f5"
  welcome-surface: "#f3e6ee"
  intro-prepare: "#f1dde7"
  intro-explore: "#d8eef0"
  intro-apply: "#e6dff0"
  review-ink: "#235563"
  review-surface: "#e7f5f7"
  accepted-ink: "#485c27"
  accepted-surface: "#eef3e4"
  rejected-ink: "#8a2445"
  rejected-surface: "#ffedf2"
  pending-ink: "#794b31"
  pending-surface: "#f9e9e1"
  neutral-status-ink: "#6b607c"
  neutral-status-surface: "#f3f0f6"
  error-surface: "#fff0f3"
  success-surface: "#f0f5e8"
  discovery-paper: "#fffbfd"
  discovery-accent: "#a53867"
  discovery-border: "#e8ddec"
  category-ojt: "#f1d2c9"
  category-learning: "#c5e8ec"
  category-applications: "#e9c7d6"
  mobile-navigation-active: "#f2dbe8"
  signin-action-hover: "#94d5dc"
  signin-glass: "#fffefaad"
  signin-glass-mobile: "#fffefac7"
  sidebar-toggle: "#f3edf8"
  sidebar-toggle-hover: "#e9dff2"
typography:
  display:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "clamp(34px, 3.4vw, 48px)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.035em"
  discovery-display:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "clamp(32px, 3vw, 42px)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.035em"
  auth-title:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "34px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "30px"
    fontWeight: 800
    lineHeight: 1.25
    letterSpacing: "-0.035em"
  title:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    letterSpacing: "-0.35px"
  body:
    fontFamily: "DM Sans Variable, sans-serif"
    fontSize: "16px"
    lineHeight: 1.65
  label:
    fontFamily: "DM Sans Variable, sans-serif"
    fontSize: "14px"
    fontWeight: 600
rounded:
  field: "12px"
  button: "13px"
  navigation: "14px"
  notice: "16px"
  panel: "22px"
  panel-mobile: "20px"
  welcome: "26px"
  intro-art: "36px"
  status: "9px"
  metadata: "8px"
  discovery-search: "18px"
  discovery-category: "23px"
  discovery-category-mobile: "19px"
  opportunity-card: "24px"
  signin-card: "28px"
  signin-card-mobile: "24px"
spacing:
  control-gap: "10px"
  action-gap: "12px"
  section-gap: "24px"
  panel-padding: "28px"
  work-padding: "24px"
  workspace-gutter: "36px"
  mobile-gutter: "18px"
  consumer-mobile-gutter: "20px"
  discovery-section-gap: "30px"
components:
  button-primary:
    backgroundColor: "{colors.deep-purple}"
    textColor: "{colors.white}"
    rounded: "{rounded.button}"
    padding: "12px 20px"
  button-primary-hover:
    backgroundColor: "{colors.purple-hover}"
  button-signin:
    backgroundColor: "{colors.turquoise}"
    textColor: "{colors.deep-purple}"
    rounded: "{rounded.field}"
    height: "51px"
  button-signin-hover:
    backgroundColor: "{colors.signin-action-hover}"
  signin-glass-card:
    backgroundColor: "{colors.signin-glass}"
    border: "1px solid #ffffffc7"
    rounded: "{rounded.signin-card}"
    backdropFilter: "blur(22px) saturate(1.18)"
  signin-glass-card-mobile:
    backgroundColor: "{colors.signin-glass-mobile}"
    border: "1px solid #ffffffd4"
    rounded: "{rounded.signin-card-mobile}"
    backdropFilter: "blur(20px) saturate(1.16)"
  sidebar-toggle:
    backgroundColor: "{colors.sidebar-toggle}"
    textColor: "{colors.deep-purple}"
    rounded: "{rounded.field}"
    width: "42px"
    height: "42px"
  sidebar-toggle-hover:
    backgroundColor: "{colors.sidebar-toggle-hover}"
  button-secondary:
    backgroundColor: "{colors.white}"
    textColor: "{colors.deep-purple}"
    rounded: "{rounded.button}"
    padding: "12px 20px"
  button-text:
    textColor: "{colors.deep-purple}"
    padding: "0"
  field:
    backgroundColor: "{colors.control-surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "11px 13px"
    width: "100%"
  navigation-item:
    textColor: "#665471"
    rounded: "{rounded.navigation}"
    padding: "11px 14px"
  navigation-item-active:
    backgroundColor: "{colors.active-navigation}"
    textColor: "{colors.deep-purple}"
  metadata-tag:
    backgroundColor: "#faf6fd"
    textColor: "#6b567c"
    rounded: "{rounded.metadata}"
    padding: "5px 9px"
  panel:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.panel}"
    padding: "{spacing.panel-padding}"
  status:
    backgroundColor: "{colors.neutral-status-surface}"
    textColor: "{colors.neutral-status-ink}"
    rounded: "{rounded.status}"
    padding: "6px 10px"
  task-entry:
    textColor: "{colors.ink}"
    padding: "18px 0"
  discovery-search:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.discovery-search}"
    padding: "9px 10px 9px 18px"
  discovery-category-learning:
    backgroundColor: "{colors.category-learning}"
    textColor: "{colors.deep-purple}"
    rounded: "{rounded.discovery-category}"
    padding: "15px 20px 18px"
  opportunity-card:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.opportunity-card}"
  intro-pagination:
    textColor: "{colors.deep-purple}"
    rounded: "{rounded.status}"
    size: "36px"
---

# Design System: ThinkMedia

## Overview

**Creative North Star: "A welcoming next step"**

Soft rounded surfaces, warm dimensional artwork and original duotone marks make career preparation feel approachable. Deep purple anchors readable actions and headings; turquoise, peach, pinks, olive and lavender give supporting surfaces their character. White navigation and pale paper keep forms, status history and real work queues easy to scan. The navigation rail can collapse to make more room, while sign-in pairs a full campus illustration with the native account form.

The user's supplied job-app screenshots and nine-color palette replace the earlier green identity. The reusable signature combines four original task-specific transparent dimensional scenes, two responsive full-scene sign-in illustrations, a rounded book logo, custom task icons and clear native controls. Student discovery gives imagery a stronger role through illustrated category tiles and real opportunity cards; company, instructor and administrator work retains its existing task-focused structure. Imagery welcomes people into the product; actual role work and its next action remain legible beside it. The North Star is descriptive language for this implementation, not a claim of separately approved brand strategy.

**Key Characteristics:**

- Rounded, welcoming surfaces with restrained tonal depth.
- Deep-purple text and actions supported by the user-pinned pastel palette.
- Distinct dimensional learning, opportunity and application artwork with custom duotone task icons.
- Real role work, readable status and direct next actions.

## Colors

A warm, playful palette uses deep purple for structure and lighter colors for atmosphere; the frontmatter holds the exact implemented values.

### Primary

- **Deep purple** anchors headings, links, primary actions, focus and the book mark. **Purple hover** supplies a lighter action-state tone.

### Secondary

- **Discovery accent** highlights the discovery headline and section links. **Turquoise** distinguishes learning and application accents and supplies the sign-in form action with deep-purple text. **Sign-in action hover** lightens that local action variant; other primary actions remain purple. **Vivid rose** supplies small emphasis in the logo and active icon details.
- **Lavender** supports inactive progress marks and quiet task illustration accents. **Olive** belongs to supporting preparation details and graphics.

### Tertiary

- **Peach**, **blush**, **pink** and **dusty rose** are the user's warm illustration palette. Tinted derivatives support welcome, task and review surfaces; do not force every palette color into a text role.

### Neutral

- **Ink** carries body text; **muted** carries supporting copy. **Paper** surrounds **white** forms and work sections. **Divider**, **panel border** and **control border** separate rows, containers and editable controls.
- **Discovery paper** supplies the mobile student-home background; **category OJT**, **category learning** and **category applications** separate its three illustrated destinations. **Sidebar toggle** and **sidebar toggle hover** give the topbar control its pale resting and hover surfaces. **Discovery border** outlines discovery cards; **mobile navigation active** supplies the current bottom destination tint.
- **Intro prepare**, **intro explore** and **intro apply** change the illustrated surface across the three introduction steps. **Welcome surface** supports the signed-in greeting.
- **Review** uses turquoise text/surface pairs, **accepted** uses olive, **rejected** uses rose, and **pending** uses peach-brown. Draft and closed states use the neutral pair. Errors use rejected ink on the error surface; save success uses accepted ink on the success surface.

**The Readable Action Rule.** Use deep purple with white for the main action; lighter palette colors need a measured readable foreground before they carry text.

**The Written Status Rule.** Always name a status in text; its tint and dot only reinforce the label.

## Typography

**Display Font:** Manrope Variable (with sans-serif fallback).  
**Body Font:** DM Sans Variable (with sans-serif fallback).  
**Label/Mono Font:** DM Sans Variable; dates and progress counts use tabular figures.

Locally bundled variable fonts combine rounded, confident headings with open body copy. Sentence case and short action labels keep the interface conversational without hiding the task.

### Hierarchy

- **Display:** the frontmatter scale belongs to introduction headings; it becomes (36px) below the tablet breakpoint and (29px, 1.19 line height) on mobile after the discovery stylesheet override. Introduction descriptions use (16px, 1.8), then (14px, 1.7) on mobile.
- **Discovery display:** the student-home heading uses its separate frontmatter role, (36px) at the compact breakpoint and (31px, 1.14 line height) on mobile. Rose emphasis stays inside the native heading.
- **Headline:** the standard page heading uses the headline token and becomes (28px) on mobile. The other-role signed-in welcome uses a fluid (28–38px) heading, then (29px) on mobile. Authentication uses its separate auth-title role, then (29px) on mobile; the large scene heading is an h2 with a fluid (28–42px) scale and (1.18) line height, becoming (31px) at the compact breakpoint.
- **Title:** second-level headings use the title role; panel headings are (19px), and work-section headings are (18px). Resource/listing detail headings retain their contextual hierarchy.
- **Body:** default paragraphs use the body role; task summaries commonly use (13–15px). Long approved resources and detail copy use roughly (65–75ch) where space allows.
- **Discovery labels:** category titles use (16px), (14px) in the wide workspace composition, then (12px, 1.35) on mobile; their supporting labels use (12px), then (11px) in wide-workspace and mobile compositions. Section headings use (21px), then (18px).
- **Label:** persistent field labels use the label token. Editable fields use (15px), increasing to (16px) on mobile; hints remain adjacent at (12px).

**The Native Words Rule.** Keep headings, labels, errors and action text as HTML; the illustration contains no interface wording.

## Layout

The desktop shell has a white fixed navigation rail, sticky topbar (74px), and centered main content with maximum width (1480px). The rail is (238px) expanded or (84px) collapsed; at viewport widths up to (1100px), its expanded width is (214px) and compact mode is the default unless an explicit preference overrides it. The topbar toggle remains reachable in both desktop states. Main content uses top padding (30px), horizontal gutters from the workspace token and bottom padding (44px). Existing other-role dashboard work retains its (1.8fr to at least 265px) grid and section gap.

At viewport widths up to (1100px), horizontal gutters become (25px), search filters use two columns and profile side content stacks. At (900px), other-role dashboard columns and suggestion rating rows stack. At (720px), the rail gives way to a (280px) drawer and fixed bottom task navigation; desktop collapse does not shrink this drawer. The topbar becomes (65px); main padding becomes (24px 18px 105px), with bottom safe-area padding on navigation. Forms and filters stack, mobile inputs grow, and long titles and references wrap. The supported narrow viewport is (360px); support remains a verification requirement, not a measurement claim here.

Student discovery fills the available main region. Its first mobile viewport prioritizes the large opportunity heading and account shortcut, search with a filter destination, three illustrated task categories, then the start of Recently posted. Preparation resources follow, then the student's applications, a profile invitation only when course or skills are missing, and approved-resource guidance. Each tile is a real destination; no metric row precedes discovery.

Main content establishes the named inline-size container `workspace`. At a content width of at least (960px), discovery uses a main column and a support column (270–310px) with a (30px) gap; the application pocket starts beside the main heading, not below the discovery sections. Search and categories fill their column. Wide-workspace category tiles use (12px 16px 16px) padding and (96px) artwork. Below that container width, discovery stacks and support uses two equal columns; at a container width up to (620px), support becomes one column. Mobile also explicitly stacks these regions. This responds to available content width as the sidebar opens or closes.

Categories use a (16px) gap, then (10px) on mobile. Student home alone uses mobile main padding (19px 20px 105px) and discovery paper. Recently posted uses two grid columns on desktop; on mobile it becomes a horizontally scrollable, mandatory snap row with a (13px) gap and cards at (83%) of its width, leaving the next card visible. Keyboard-accessible detail links remain inside each card. Learning previews use image/copy columns (105px and remaining width), reducing to (83px and remaining width) on mobile. This hierarchy is scoped to student home, not every role or screen.

The introduction fills its entire viewport with the active step color: blush for Prepare, turquoise for Explore and lavender for Apply. Supporting text darkens to retain contrast on these colored backgrounds. The introduction uses a wide header (1260px maximum) and two-column body (1150px maximum), with illustration and copy in a (1.1fr to 1fr) ratio. On mobile the art precedes the copy in one column, with (22px) page gutters and a flexible full-width Next action. Wider screens at a minimum of (1500px) gain a larger introduction top offset. Authentication is a full-viewport scene, not a split panel. On desktop, a fixed cover background fills the screen: the student anchors the left, while a soft lavender garden and a pale right-side wash keep the account form legible. The native form sits in one glassmorphism card on the right (maximum width 510px, 28px radius, translucent warm-white fill, 22px backdrop blur, fine white border and quiet shadow). The logo and short welcome copy sit directly on the image without separate badges or caption cards. The form card stays inside the viewport; long create-account content scrolls inside the card. At widths up to (800px), the card centers and the text scales down. At (600px), switch to the portrait `<picture>` asset in a (250–340px) top image region; put the same glass card below it on the soft blush page background. Fix the viewport to (100svh), keep page/body scrolling off, and let only the form card scroll with `overscroll-behavior: contain`. Set the card content to start at its top (`justify-content: flex-start`) so the title, role field and first input are visible when registration opens. Keep image proportions with `object-fit: cover`; never force the landscape source into the phone banner or size its background against the growing registration page.

## Elevation & Depth

Depth comes chiefly from pale surface layers, hairline borders and the softly sculpted artwork. Ordinary work panels have no resting shadow. Selected authentication tabs use a small shadow (`0 3px 9px #402c7510`); the open mobile drawer uses an offset shadow (`10px 0 30px #402c7526`) with a purple translucent backdrop. Illustration lighting stays inside the artwork. The mobile bottom bar has a small upward shadow (`0 -4px 18px #402c7509`) and rounded upper corners; discovery cards remain flat. Collapsed-rail tooltips use `0 5px 14px #402c7520`. The fixed sign-in background gets a light horizontal wash on its right side so labels and links stay readable without a separate text panel. On mobile, the portrait illustration fades into the blush page above the glass form card.

**The Quiet Surface Rule.** Let rounded tonal surfaces and artwork carry depth; keep work panels flat at rest.

## Shapes

Soft rectangles are the recurring form: fields and buttons use their dedicated rounded tokens, navigation is a little fuller, and panels have broad corners that tighten on mobile. Status and metadata shapes are compact rounded rectangles. The greeting surface uses the welcome token (24px on mobile); introduction artwork has broad corners (29px on mobile). The sign-in glass form card uses (28px) corners on desktop and (24px) on phones; the scene image itself is full bleed and has no enclosing card radius. Task emblems are compact colored tiles with rounded outlined symbols. Student discovery expands these into broad illustrated category surfaces with dedicated category radii; search uses its own rounding. Opportunity cards use the opportunity-card token, tightening to (23px) on mobile; learning previews use (21px), then (20px). Borders are generally one pixel; the surrounding interface stays flat while the sign-in scene uses its text-contrast overlay.

## Components

### Buttons

Confident and tactile. Primary actions use deep purple and white; secondary actions use white, purple text and a pale purple border. Shared padding and rounding come from frontmatter, with a minimum height (46px). Hover changes the surface; keyboard focus uses a purple outline (3px) with offset (4px). Disabled controls dim and retain native disabled behavior. Inline text actions underline on hover. The welcome action is a white variant on the blush surface. Mobile introduction Next is at least (48px) high. The sign-in form has a turquoise primary variant with purple text, (51px) minimum height and (750) weight; its hover color stays local to authentication.

### Chips

Quiet labels with a clear purpose. Metadata tags use a pale surface, purple-gray text and a thin border. Status chips pair a six-pixel dot with a written state and the semantic colors above. Learning Save and React controls retain explicit pressed states, with a rose selected surface.

### Cards / Containers

Roomy without hiding work. White panels use the panel radius, panel border and padding tokens. Work sections use the work padding and a section gap below; mobile panels reduce to (22px 18px) padding and the mobile panel radius. Rows stay connected inside each section, with wrapping text, clear destinations and visible empty, loading and request-error states.

### Student discovery

Illustration accompanies a functional destination. The categories lead to OJT-only browse (`type=ojt`), learning and the student's own applications. Search submits the real keyword query, and its adjacent filter control opens opportunity browse. Recently posted loads up to four published listings; card text comes from listing records and includes company, role, location, up to two skills and a detail link. It is a recent-record view, not a personalized ranking. Preparation previews load up to three published resources; the application pocket loads only the authenticated student's records and shows up to three. Loading copy, explicit empty states and a retryable partial-load alert preserve the real data state. Artwork supplies no fabricated pay, employer, count or acceptance claim. This implements FR02–05/08 with NFR05/09; suggestions remain a separate destination.

### Inputs / Fields

Persistent labels above lightly tinted controls. Use a visible control border, field rounding, native autocomplete and an adjacent hint/error. Invalid fields retain the implemented red border; error notices use the rose semantic treatment. Password visibility is a named button. Recoverable failures preserve valid input and keep the next action available.

### Navigation

White rail, muted purple-gray labels and original rounded icons. Active destinations use a pale lavender surface, deep-purple label and vivid-rose icon accent; hover is a subtler tint. Stable hash URLs preserve route and detail location. The desktop rail toggle exposes its current expansion state and controlled sidebar. Collapsed destinations retain accessible names; hover and keyboard focus reveal fixed purple tooltips with white text (12px, 1.4 line height), (9px) corners and (9px 12px) padding. Compact-rail labels remain visible when hovered and dismiss with Escape without moving keyboard focus. Mobile has a bottom task bar plus a full drawer with Escape, focus containment, background scroll lock and return to its opener. Closing or resizing restores the previous document overflow; leaving mobile closes the drawer and returns focus to the desktop toggle. Account navigation and sign-in expose Getting started to replay the introduction. The mobile task bar has rounded upper corners (21px) and the active tint documented above. Student search and listing filters use URL query parameters; selected search/type/skill/location state survives reload, listing detail and back navigation, while Clear resets the filter state.

### Original marks and illustration

The book-and-leaf mark uses a rounded deep-purple tile with white pages, turquoise leaf and rose dot. Eleven custom SVG task marks share rounded strokes and small colored fills. Both mark families are in `frontend/src/brand.tsx`; utility icons elsewhere remain compatible with the outlined visual language. Opportunity and learning emblems identify content kinds, never fictional employer brands.

Original WebP assets live in `frontend/public/illustrations/`; generated assets have an adjacent `.webp.json` provenance record:

| Asset | Native dimensions | Scene and implemented role |
| --- | --- | --- |
| `thinkmedia-welcome.webp` | 960 × 877 | Transparent seated student with laptop; Prepare introduction and other-role welcome. |
| `thinkmedia-opportunities.webp` | 960 × 960 | Young man with career materials and oversized briefcase; Find OJT category, opportunity covers/details and Explore introduction. |
| `thinkmedia-learning.webp` | 960 × 960 | Books, study objects and graduation cap; learning category, resource previews/details and guidance. |
| `thinkmedia-applications.webp` | 960 × 960 | Clipboard, folder, pencil and paper plane; applications category/empty state, alternating content covers and Apply introduction. |
| `thinkmedia-signin-background.webp` | 1800 × 1013 | Desktop full-viewport botanical campus scene; student and books left, open garden space right. |
| `thinkmedia-signin-mobile.webp` | 1024 × 1280 | Purpose-composed portrait version for the phone banner; keeps the student proportional and fades into blush at the bottom. |
| `thinkmedia-signin-scene.webp` | 1024 × 1365 | Earlier portrait study scene retained as an unused source asset; do not use for the current sign-in layout. |

The learning, opportunity, application and both current sign-in provenance files record `image_gen`, the source path, prompt and decorative-use restriction; the welcome provenance records its prompt and creation time. They are generated illustration, not photographed participants, employer branding or research evidence. Use the task-appropriate asset rather than repeating the welcome scene everywhere. Images contain no interface wording and use empty alternative text beside meaningful native labels. The shared `Artwork` component reserves a square (960 × 960) box, eager-loads priority art and otherwise lazy-loads; its welcome asset is intrinsically shorter. The four transparent task assets use `object-fit: contain` to preserve the composition. The desktop background uses `thinkmedia-signin-background.webp` with `background-size: cover` and `background-attachment: fixed`, independent of registration form height. On phones, a `<picture>` source selects `thinkmedia-signin-mobile.webp`; its fixed-height banner uses `object-fit: cover` and `object-position: center 37%`. Never stretch a landscape image to fill the phone banner.

### Illustrated sign-in

The screen uses one continuous botanical campus image across the desktop viewport, with a fixed light wash at the right for contrast. Keep the art full scene; do not divide it into an image panel plus blank page. Put the real sign-in or registration form in one warm-white glassmorphism card, with translucent fill, backdrop blur, white hairline border, 28px desktop / 24px phone corners and restrained shadow. Do not put the logo or welcome caption in additional cards. The logo and short scene heading are native HTML directly over the left-side image. The h1 belongs inside the form card and reads “Welcome back.” or “Create your account.”

Phone screens show the sign-in scene as a compact banner above the same glass card, fading into the blush page surface. The card overlaps the banner slightly and the document scrolls naturally, so the footer and every create-account field remain reachable without clipping or a nested scroll area. Keep the title and first field initially visible, preserve keyboard access, and prevent horizontal overflow.

Sign in/Create account mode buttons retain pressed state, password visibility remains a named button, and actual role selection, validation, errors, autocomplete and privacy copy remain part of the existing workflow. Authentication fields are at least (50px) high; mobile input text is (16px). Artwork is decorative and never replaces labels or native copy. Reference-only social providers and password recovery controls are not presented as working features. Scope: FR01–02/W01 with NFR03/05/09. Visual references: `.impeccable/review/signin-fullbg-desktop.png`, `signin-fullbg-mobile.png`, and `signup-fixed-phone.png`.

### First-use introduction

Three optional steps explain Prepare, Explore and Apply, using the welcome, opportunity and application scenes respectively. Skip introduction and Sign in provide immediate entry; Next, Back and named progress buttons support deliberate movement. The active step exposes `aria-current="step"`; changing steps focuses the heading. The visual topic labels are decorative, while the progress controls are native buttons. Signed-in replay ends with Go to workspace.

Copy arrives with a brief vertical movement (0.35s, cubic-bezier(0.16, 1, 0.3, 1)); the art surface changes color (0.3s ease-out), and the active progress bar changes width (0.2s ease-out). Reduced motion removes animations and transitions. Ordinary interactive color transitions use (0.15s), and the drawer uses (0.2s). Rail width, padding and workspace offset transition over (0.18s ease-out); the mobile drawer uses (0.2s ease-out). Reduced motion removes these transitions. Introduction and nonpersonal rail preference persistence are recorded in PRODUCT.md.

## Do's and Don'ts

### Do:

- **Do** preserve the user's rounded, illustrated job-app direction and nine-color palette.
- **Do** anchor readable actions and headings in deep purple, with pale secondary surfaces.
- **Do** use the distinct original artwork for its task and keep custom task icons consistent.
- **Do** preserve the student discovery hierarchy and horizontal mobile opportunity cards within that surface.
- **Do** pair real role work with clear next actions, written statuses and Asia/Manila dates.
- **Do** keep introduction entry, skip, back and replay controls visible and usable.
- **Do** preserve labels, keyboard focus, reduced motion and recoverable task states.
- **Do** keep the desktop rail toggle reachable and the mobile drawer full width within its established (280px) size.
- **Do** use the full-scene desktop illustration, dedicated portrait mobile art, and one translucent form card; let only that card scroll on registration.

### Don't:

- **Don't** restore the obsolete green identity as the primary visual direction.
- **Don't** use light palette colors for small text without measuring contrast.
- **Don't** copy reference wording errors, inactive controls, fictional salaries, partner logos or invented job counts.
- **Don't** treat decorative student artwork as participant evidence or a hiring promise.
- **Don't** replace actual application history, private-file controls or authorization with decorative UI.
