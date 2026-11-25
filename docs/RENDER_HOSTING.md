# ThinkMedia online demo

The Render demo runs the React build and FastAPI application in one Docker web
service. PostgreSQL stores sessions, profiles, learning records, quizzes,
applications, private PDF bytes, and review history. The service uses the free
compute plan in Oregon.

**Live demo:** https://thinkmedia-demo-m74t.onrender.com.
The November 25 [hybrid recommender](HYBRID_RECOMMENDER.md) shares runtime and
offline scoring. The provisional default blend is0.5, with profile-only cold
starts. No genuine accuracy or satisfaction result is claimed. The appearance
toggle in the sidebar, mobile More page and sign-in screen remembers a browser's
light/dark preference locally.
The November 24 refinement adds confirmed workspace assistance and a fictional
opportunity catalog. See [assistant actions](API_ASSISTANT_WORKSPACE.md).
The first successful deployment used commit `f6ed08e`, on November 23, 2026
(Asia/Manila). Current checks are in the
[November 24 assistant report](QA_ASSISTANT_WORKSPACE_2026-11-24.md), with the
earlier [requirements audit](REQUIREMENTS_COVERAGE_2026-11-23.md) retained.

## Deployment

The repository-root render.yaml describes the service. The Docker build runs
npm ci and the TypeScript/Vite production build, then installs the Python
runtime requirements. The runtime serves the frontend alongside /api/v1
and /health.

The container runs as an unprivileged user. Startup serializes schema migrations
with a PostgreSQL advisory lock and starts one Uvicorn process on 0.0.0.0:$PORT.
Render supplies HTTPS and RENDER_EXTERNAL_URL. The app uses that exact origin
for CSRF validation and sets secure, HttpOnly session cookies.

The approved free configuration uses a separate logical database and restricted
login inside the existing PostgreSQL instance. The application login has no
superuser, database-creation, or role-creation privileges. It owns ThinkMedia's
database. Its bootstrap owner has the approved membership needed to create that
database. Keep database connection URLs outside Git.

## Runtime settings

| Variable | Purpose |
| --- | --- |
| DATABASE_URL | ThinkMedia PostgreSQL URL. Standard postgres:// and postgresql:// URLs are normalized to the installed psycopg driver. |
| APP_ENV=demo | Hosted demonstration mode with secure cookies. |
| APP_CSRF_SECRET | Persistent, generated session-bound CSRF secret. |
| APP_ALLOWED_ORIGINS | Additional exact origins. The Render application origin is included automatically. |
| APP_ASSISTANT_MODE=external | Enable live source-grounded Guidance. |
| APP_ASSISTANT_TOOLS_ENABLED=true | Allow bounded workspace tools and confirmation previews; false retains guidance without assistant actions. |
| APP_ASSISTANT_PROVIDER_PROFILE=groq_openrouter | Try Groq first, then OpenRouter. |
| GROQ_API_KEY, OPENROUTER_API_KEY | Server-only provider credentials. |
| GROQ_MODEL | Defaults to openai/gpt-oss-20b. |
| OPENROUTER_MODEL | Defaults to nvidia/nemotron-3.5-super-vl:free. |
| APP_ASSISTANT_CALL_BUDGET=100 | Shared attempt cap for both routes, per process lifetime. Failed attempts consume the cap. |
| APP_ASSISTANT_TIMEOUT_SECONDS=30 | Combined transport deadline allocated between configured routes. |
| APP_ASSISTANT_MAX_COMPLETION_TOKENS=1024 | Output cap for each attempt. |
| APP_BOOTSTRAP_DEMO=true | Explicitly provision dedicated fictional accounts and learning examples at startup. |
| APP_DEMO_ADMINISTRATOR_PASSWORD | Private password for presentation-administrator@example.test. |
| APP_DEMO_INSTRUCTOR_PASSWORD | Private password for presentation-instructor@example.test. |
| APP_DEMO_STUDENT_PASSWORD | Private password for presentation-student@example.test. |
| APP_DEMO_COMPANY_PASSWORD | Private password for presentation-company@example.test. |

Passwords are generated independently. Demo initialization preserves existing
passwords and edits, verifies the dedicated account identities, and creates
three published lessons plus three instructor drafts once. The demonstration
company starts pending so administrator verification can be shown.

On the prepared workstation, the four actual hosted passwords are saved in
`.local/render-demo-passwords.private.env`. This ignored file contains only demo
passwords. It is separate from local presentation credentials. In Render,
the same values are on the service's Environment page. Keep them private.
Use separate browser profiles for each role.

The November 24 private access sheet is `.local/hosted-access.private.md`. It
contains instructor and administrator access, a verified fictional catalog
organization at `presentation-catalog-company@example.test`, and the separate
pending company used for verification demonstrations. The catalog password is
distinct and derived from the private company runtime secret with a fixed HMAC
domain. No additional environment secret is needed; no existing password is
reset. Never put the access sheet in the deck or repository.

The catalog organization has six published fictional opportunities (four OJT
and two job examples) and one editable draft. Titles, requirements and company
description identify them as fictional. Initialization preserves changes,
applications and later verification decisions. The original pending company's
state is preserved for the administrator walkthrough.

The Learning Library contains three published practice lessons: résumé project
bullets, STAR interview answers, and workplace progress updates. Each includes
a reference link and a scored quiz. The résumé lesson includes the fictional
PDF. The instructor's **Teaching materials** page contains three editable lesson
drafts plus a clearly labeled skill draft created by the hosted smoke test.
The November 24 live checks also left editable fictional lesson drafts.
Use **New skill category** or **New lesson**, save, and submit for review.
An administrator publishes through **Learning content → Review instructor submissions**.

Guidance receives a question, up to three preceding questions, and up to three
approved public excerpts. Private account, profile, application, and PDF objects
are excluded. Each returned citation must match the retrieved sources. Each
configured provider is tried once. Unavailable providers yield a recoverable
error while other workflows remain available.

## Free-service operating limits

The free web service can sleep after 15 minutes of inactivity and may take time
to restart. Its filesystem is temporary. Database records and PDF attachments
survive service restarts because they reside in PostgreSQL.

The shared free PostgreSQL instance has a 1 GB capacity and expires on
December 22, 2026. The workspace's free instance hours and build allowances are
shared by its services. A free instance does not supply managed backups.
Back up ThinkMedia before the expiry date. An always-on deployment, managed
backup retention, and a real-data pilot require further operating decisions.

The application includes explicit backup/restore and retention tools. Existing
local-only operations intentionally reject remote targets. On the prepared
workstation, run the dedicated hosted export from the repository root:

```powershell
& ./scripts/backup-render.ps1
```

It reads the approved ThinkMedia-only connection from ignored local settings,
requires TLS, and stores custom-format exports in `.local/hosted-backups`.
Incomplete exports retain a `.partial` suffix. Completed files end in `.dump`.
The Windows task **ThinkMedia hosted database backup** runs daily at 02:00
UTC+8, with StartWhenAvailable for missed runs. Its manually triggered check
returned result 0. It requires this workstation, its signed-in user, network,
the private settings, and the local Python/PostgreSQL tools. It cannot guarantee
a 24-hour recovery point while the workstation is unavailable. The November 23
backup was restored into a new disposable local database: all 22 public-table
counts and both PDF byte fingerprints matched. The November 24 backup includes
the assistant migration; restoration matched all 23 public-table counts and both
PDF fingerprints. Existing databases were not overwritten.

The private backup log is `.local/hosted-backup.log`. Backups contain account
hashes and private demo records; keep them outside Git and approved sharing.
Real privacy, retention, and company-verification policies require
owner approval. The public demo should use fictional records.

Sources used for this configuration are Render's
[Blueprint specification](https://render.com/docs/blueprint-spec),
[Docker guide](https://render.com/docs/docker),
[environment variables](https://render.com/docs/environment-variables), and
[free service limits](https://render.com/docs/free).
