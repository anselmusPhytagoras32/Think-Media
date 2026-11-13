# Learning library and company identity

November 14 update: this is a historical design record. The owner requested
removal of all placeholders. The special demo-company logo and mock labeling
described below have been removed; every company now uses its saved name and
derived initials. The local database has been reset except for administrator
accounts. See [Local reset](../LOCAL_RESET.md).

FR03/04/08; W02/W03; NFR05/09/10.

## Learning

The library leads with a compact illustrated welcome, keyword/topic search,
shortcuts from actual published-resource tags, and resource cards. Personalized
suggestions occupy a separate For you view, preserved through detail/back.
Search values survive detail/back as well. Save, react, quiz, report and
administrator publication controls continue to call the existing APIs.

`ResourceArtwork` selects decorative imagery from title/tags, shared between
home previews, library cards and resource details. It never uses card order or
invents an employer author. Unknown topics use the existing learning illustration.

Three original 3D clay scenes were generated with the built-in `image_gen` tool:

| Topic | Asset and exact prompt record | Brief |
|---|---|---|
| Coding/data | [Image](../../frontend/public/illustrations/learning-coding-data.webp), [prompt](../../frontend/public/illustrations/learning-coding-data.webp.json) | Laptop/code brackets, database stack and connected data blocks. |
| Web/portfolio | [Image](../../frontend/public/illustrations/learning-web-portfolio.webp), [prompt](../../frontend/public/illustrations/learning-web-portfolio.webp.json) | Portfolio monitor, responsive layout objects and design tablet. |
| Application preparation | [Image](../../frontend/public/illustrations/learning-application-prep.webp), [prompt](../../frontend/public/illustrations/learning-application-prep.webp.json) | Resume folder, review/checkmark and internship briefcase. |

All use the established plum, teal, peach and cream palette and matte rounded
materials, with native text outside the artwork. Optimized assets total about
122KB and reserve 960x720 dimensions. Source generations remain outside the repo.

## Company branding

An original vector DP mark represents the explicitly fictional Demo Practice
Studio. The same logo file and actual company identity appear on Recently posted
cards, opportunity result rows and listing details. Multiple listings from that
company share its mark; different job titles never imply different employers.

Other companies get their own name-derived monogram fallback, rather than the
demo studio logo. Published eligibility and company verification still come from
the existing backend. The branding code does not create, verify or rename records.
The mock cover is labeled Mock company and retains the actual company name below.

## Verification

The 35-test Chrome suite initially passed 32 checks and exposed a visible-label
mismatch on cover buttons plus a test's assumption about listing order. Cover
button names now begin with their visible Guide/Guide & quiz badge. The logo test
targets the intended company explicitly and verifies its logo source/ID across
home, details and results; a separate fixture checks other-company fallback.
The company check then passed; both affected accessibility/library checks passed
after correcting the final accessible-name wording. All 35 browser checks have
passing evidence across the full run and these focused reruns.

Native rendered checks at 1440, 768 and 360px show semantic artwork for all three
seed topics, connected company logos and no horizontal overflow. Local screenshots
are `.local/learning-*.png` and `.local/company-home-*.png`. TypeScript/Vite builds
passed; Impeccable detectors reported no findings on the changed surfaces.
