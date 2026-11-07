# ThinkMedia local MVP interface

## Priority issues

| Severity | Finding | Heuristic | Change | SRS basis |
| --- | --- | --- | --- | --- |
| Major | Home shows promotional slogans and repeated profile prompts without current work | Match between system and real world | Give each role its actual work queue, next action, recent applications or published resources; show real totals only | PD7 7.6; W02–W05/W08 |
| Major | Navigation lives only in component state, so reload and browser Back lose location | User control and freedom | URL-backed role navigation and resource/application detail links, with working Back behavior | PD7 7.6; UC03–UC06 |
| Major | Review application repeats the upload form without a clear summary and validates file bounds late | Error prevention | Validate the file before review; show selected filename, recipient, cover letter and privacy consequence; preserve edits after failure | W04; FR05 |
| Minor | Rejected, accepted and draft records all use the same pale badge | Visibility of system status | Distinct labeled status treatments and readable history; explain the next allowed action | W04–W05; FR07 |
| Minor | Mobile users repeatedly open a long drawer for frequent tasks | Flexibility and efficiency | Persistent role-specific mobile navigation for frequent tasks; retain accessible drawer for remaining destinations | NFR05/09; 360px |
| Minor | Learning content requires opening a resource before saving/reacting | Recognition rather than recall | Put explicit save/react actions on feed entries, retain the full reading and quiz view | W02; FR03 |
| Cosmetic | “Next chapter”, decorative arch and repeated generic encouragement occupy task space | Aesthetic and minimalist design | Use concrete OJT labels, compact hierarchy and useful activity; retain the established green identity | PD7 W01–W08 |

## Preserve

Keep the real FastAPI/PostgreSQL integration, server authorization, private attachments, controlled transitions, English/Asia/Manila presentation, native form semantics, contrast-corrected focus and honest resource-lookup labeling. Do not add cloud work or invented demo statistics.

## Verification

Actual local browser workflows, 360px/desktop captures, keyboard navigation and axe scans. This is an implementation/source assessment, not observed user research or a claim of measured usability improvement.

## Resolution

All listed changes are implemented in the local MVP. The final 12-test browser/API suite and production build passed. An independent source/browser review found three additional route/form recovery defects; all were corrected and independently rechecked as resolved. See [verification evidence](thinkmedia-verification.md) for commands, captures and limitations. The findings remain an implementation assessment, not observed participant research.
