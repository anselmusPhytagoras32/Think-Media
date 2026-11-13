# Guidance conversation — November 13, 2026

## Layout and tone

The guidance surface prioritizes asking, reading an answer and checking its
sources. “Your OJT guide” connects the small panel to the product's preparation
purpose. The existing learning illustration, purple book mark, lavender header
and topic-specific icons add the same personality as the student workspace.
No generated answer, online-status claim or human adviser identity is simulated.

The empty state has three suggested questions: interview preparation, resumes
and workplace skills. Selecting one fills and focuses the question field; it
does not send a request. A short privacy hint remains beside the composer.
The latest ten exchanges stay in page memory; no conversation or draft is
written to localStorage. Clear removes the exchanges while keeping a typed draft.

## Conversation and controls

The header and composer stay fixed within the guidance surface. Only the
conversation scrolls. Questions align right; responses carry the book mark,
actual response mode, source buttons and uncertainty when returned by the API.
Long answers wrap. Sources open as inline, focused previews with a close action
that restores focus to the source button. Optional satisfaction feedback opens
only when requested and still requires explicit submission.

The send action has a visible disabled state and an accessible name. A request
shows a written progress message and an icon whose rotation is removed for
reduced motion. Failure preserves the draft/question and offers retry of the
original question. Existing status announcements and marketplace recovery copy
remain. The composer grows to 120px before its own text scrolls. Enter submits
with a fine pointer; Shift+Enter adds a line. Touch users have a 44px send action.

## Responsive behavior and focus

Above 720px, a nonmodal native dialog is anchored above the Guidance launcher.
It is 440px wide and bounded by the viewport, with an optional 700px expanded
view. The workspace remains usable alongside it. Below that breakpoint, the
same conversation becomes a native modal sheet, eight pixels inside the visible
viewport. Browser modality contains focus and makes the underlying app inert.
Closing or pressing Escape restores focus to the launcher and restores body
scrolling. Resizing switches modality without discarding the conversation.

VisualViewport resize/scroll events adjust the mobile sheet's height and top
position as the available viewport changes. Short viewports omit decorative art
and retain the message scroll area and composer. Physical phone keyboards still
need device verification; desktop Chrome viewport emulation is not that evidence.

The standalone guidance route uses the same conversation component. It retains
its page heading and bounded scroll area; it does not duplicate a second live
assistant instance beside the floating panel.

## Requirements and verification

FR10/W07: approved-resource answers, citations, uncertainty, loading, recovery
and read-only interaction. FR12: voluntary satisfaction intake is preserved.
NFR03/11: private bounded page-memory conversation. NFR05/09: 360px layout,
labeled controls, native modality, Escape/focus restoration and announcements.

Implementation: `frontend/src/guidance.tsx`, the guidance shell in
`frontend/src/main.tsx`, and `frontend/src/guidance-bubble.css`. The old assistant
was extracted from the learning module. The November 14 functional correction
adds bounded preceding questions and relevance-ranked published passages to the
provider context; see `docs/API_LEARNING.md`.
Intent, Impeccable and Articulate guided hierarchy, responsive presentation and
copy. Include's keyboard/focus guidance informed modal verification.

Focused acceptance: seven existing learning/administration/accessibility/
requirements checks passed. Three new layout/interaction tests passed after a
test locator was narrowed from a general accessible label to the textbox role.
They cover 360×800, 390×844, 768×900, 1440×1000 and 844×390, desktop expansion,
draft preservation, source focus, long text, pending/error/retry and clearing.
Axe scans passed for empty desktop/mobile and a long mobile answer.
The production build passed. Impeccable's detector reported `[]`.
The final full browser regression run passed all 42 tests in approximately two
minutes, with zero skipped, unexpected or flaky tests. Its machine report is
`.local/qa-guidance-redesign.json`.

Local rendered evidence: `.impeccable/review/guidance-new-1440.png`,
`guidance-new-360.png` and `guidance-new-answer-360.png`. The long answer is an
explicitly synthetic stress fixture. Browser checks use isolated API8001 and
frontend5174, with external provider calls disabled. They are not AI research
measurements or live-provider quality assessments.
