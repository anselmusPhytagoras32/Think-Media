# Hybrid recommender and appearance verification — November 25, 2026

The owner requested a simple dark mode and completion of the hybrid recommender
against the six project objectives. The fixed proposal and presentation were
not edited. See [hybrid implementation](HYBRID_RECOMMENDER.md) for the objective
mapping and [appearance behavior](ux/appearance.md) for theme controls.

## Functional changes

FR02/08/09/12, NFR03/06/08/11: matching now includes student professional
background, listing requirements and public employer descriptions. The existing
TF-IDF/cosine and explicit-rating collaborative workflow uses one shared scoring
module in runtime and evaluation. A provisional configurable 0.5 blend enables
collaborative contribution when eligible feedback exists; cold-start items use
profile-only scoring. Components, actual strategy, effective alpha and readable
reasons are returned without peer identities or private application data.

Chronological five-fold evaluation fits text and neighbors on earlier training
data, selects each fold's weight on a separate validation block, and evaluates
untouched later observations. MAE/RMSE, profile-only and item/global-mean baselines,
coverage, split times and provenance are recorded. The grouped cold-start
protocol remains separate. Empty features and missing genuine datasets are
handled without inventing measurements. Existing CSAT/BERTScore tools retain
their separate human-review and genuine-data conditions.

NFR03/05/09: a browser-local light/dark preference is available at sign-in, in
the sidebar and on mobile More. It is applied before rendering, persists across
reloads and synchronizes across tabs. Storage failures do not prevent switching
the current page. Existing light values remain fallbacks; illustrations retain
their colors. No database migration or account-field change was required.

## Verification

- **289 backend tests passed in 834.89 seconds.** Alembic reported no new upgrade
  operations. This includes matching/feedback tests, configured hybrid ranking,
  observed-only neighbors, background/requirements matching, employer background,
  unauthorized access and the existing marketplace/assistant negative cases.
- **57 Edge browser tests passed in 594.71 seconds**, against the disposable local
  API/database. These include three new theme tests, all-role access, student
  recommendations and optional ratings, guidance, mobile layouts and existing
  cross-role workflows.
- **11 evaluation integrity tests passed.** They cover grouped separation,
  training-only text fit, chronological fold boundaries, validation-only weight
  selection, missing ratings, empty features, CSAT validation and separate human
  factual-review accounting.
- The production TypeScript/Vite build and `git diff --check` passed. A private
  value scan found no configured keys/passwords in changed files or the built
  frontend.
- Theme-specific automated axe checks found no serious or critical findings in
  the checked sign-in, student, instructor, company and administrator views.
  Desktop/mobile screenshots were inspected. These are automated/visual checks,
  not real assistive-technology user evaluation.

The first new matching test reproduced a general fallback despite a matching
professional background. The new shared-model/fold imports were absent before
implementation. A new empty-feature evaluator check also reproduced a missing
vocabulary error before correction. The appearance test initially failed because
the toggle did not exist. These regressions pass after their changes.

Commands, after explicitly selecting disposable local database settings:

```powershell
cd backend
./.venv/Scripts/python.exe -m pytest -q --junitxml=../.local/hybrid-backend.xml
./.venv/Scripts/python.exe -m alembic check
cd ..
./backend/.venv/Scripts/python.exe -m unittest evaluation.test_evaluation -v
./backend/.venv/Scripts/python.exe evaluation/hybrid_demo.py --output .local/hybrid-synthetic-demo.json
cd frontend
npm run build
$env:PLAYWRIGHT_CHANNEL = 'msedge'
$env:PLAYWRIGHT_API_TARGET = 'http://127.0.0.1:8003'
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5175'
npm test -- --reporter=line,junit
```

Private XML and screenshots remain in ignored `.local` storage. Runtime secrets
and credentials remain outside Git.

## Hosted verification

Render marked application commit `4a51bb6` Live at
https://thinkmedia-demo-m74t.onrender.com. A read-only check using the fictional
student account confirmed `hybrid-v2`, configured alpha0.5, provisional weight
status, six published opportunity results and three learning results. Component
scores and effective fallback weights were bounded and consistent.

The hosted dataset had zero explicit ratings at this check. Its actual mode was
therefore `profile`, not artificially forced to `hybrid`. No synthetic ratings
were inserted into the hosted database. The active hybrid branch was verified
through the isolated integration fixtures and shared-model evaluation above.

An isolated Edge browser also verified dark-mode persistence at sign-in, the
actual Suggestions page, 360-pixel containment and switching back to light mode
through mobile More. It found no serious/critical axe findings or browser runtime
errors. Hosted desktop/mobile screenshots were visually inspected. The first
private harness attempts left an already-mounted signed-out page unchanged after
HTTP-client login; reloading to initialize its account state corrected the test
setup. No application change was required for that harness issue.

See the [sanitized verification receipt](../backend/reports/hybrid-appearance-2026-11-25.json)
for aggregate local/hosted results. Research metrics remain unmeasured.

## Evaluation limits

The synthetic demonstration contains 168 generated observations across five
folds; 99 test observations had collaborative coverage. It demonstrates the
statistical pipeline only. It is explicitly labeled synthetic and does not
represent participants, real feedback or research findings. No artificial
ratings are added to the hosted demo to force a hybrid label.

Genuine MAE/RMSE, cross-validation findings, CSAT, BERTScore and human factual
review remain pending. A fresh account normally receives profile/general results
until enough shared explicit feedback exists. A high CSAT score or optimal blend
cannot be established by implementation alone. No placement, effectiveness or
production-readiness claim is made.
