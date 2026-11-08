# ThinkMedia

React + FastAPI + PostgreSQL career and OJT workspace. Product requirements are in [PRODUCT.md](PRODUCT.md); verified progress and remaining work are in [implementation status](docs/IMPLEMENTATION_STATUS.md).

For the prepared **Windows + Ubuntu WSL local presentation**, follow the
[presentation startup and acceptance guide](docs/PRESENTATION_READINESS.md).
The backend virtual environment in this checkout is Linux-based; it does not
contain Windows `Scripts/Activate.ps1` executables.

## Run the application directly

Set up a local PostgreSQL database and backend environment using [backend setup](backend/README.md). Apply migrations only to a disposable local/development database:

```bash
cd backend
.venv/bin/alembic upgrade head
APP_ASSISTANT_MODE=retrieval .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. The React client proxies API requests to FastAPI on port 8000 and uses real PostgreSQL persistence. No frontend mock server is required. Administrator accounts are provisioned separately using the backend CLI.

## Verify

```bash
cd frontend
npm run build
npx playwright install chromium
# Start the separate disposable browser API on port 8001 first.
PLAYWRIGHT_API_TARGET=http://127.0.0.1:8001 PLAYWRIGHT_BASE_URL=http://127.0.0.1:5174 npm test
```

Browser tests require the API, a disposable development database, and the synthetic test administrator described in [frontend setup](frontend/README.md). Backend pytest uses a separate disposable PostgreSQL database; see [audit evidence](backend/reports/codex-audit.md). Never run test cleanup against production.

The legacy orchestration tools below remain as historical repository material. They are not needed for startup or current implementation; do not run `./team`, `orchestrator.py`, or external headless workers for this workflow.

## Current verified scope

Accounts and profiles, company verification, published OJT/job listings, private PDF applications and applicant review, learning resources/quizzes/moderation, real suggestions/ratings and source-backed resource lookup work against FastAPI/PostgreSQL. External AI is off by user choice. Research metrics remain pending genuine datasets. See [verified status](docs/IMPLEMENTATION_STATUS.md), [operations](docs/OPERATIONS.md) and [evaluation](docs/EVALUATION.md).

## Legacy agent-pack instructions

# ThinkMedia — Codex / Antigravity / OpenCode agent pack

This pack **adapts the prior one-repo Codex CLI supervisor to the uploaded ThinkMedia SRS**. It does not create a new repository, make calls to OpenAI APIs, or change your existing application source. It does *not* contain the original full DOCX; the compact agent brief is included.

The manager uses your **ChatGPT-authenticated `codex exec -m gpt-6.1-sol`**. Two implementation workers are Gemini 3.8 Flash through Antigravity CLI (`agy`) and DeepSeek V4.1 Flash through OpenCode (`opencode`). Their exact model IDs and account eligibility should be verified on your system.

## 1. Preparation

From the **root of your existing Git repository** (WSL/Linux is required for the starter's `fcntl` locking):

```bash
codex login status
agy models
opencode models
```

If not installed/authenticated, follow the respective official CLI instructions. OpenCode may require a separate DeepSeek provider subscription/API key; Codex ChatGPT login does not pay for other model providers. The ThinkMedia **in-app AI career assistant** independently requires an external LLM provider for runtime; agent accounts cannot automatically power that feature.

Install both skills and verify that Antigravity can actually read them:

```bash
npx impeccable install
npx skills add ghaida/intent --all
find .agents/skills -name 'SKILL.md'
agy -p 'Find and open the installed Intent and Impeccable SKILL.md files; do not edit anything.' \
  --model gemini-3.8-flash-medium --output-format json
```

## 2. Add the pack to your existing repo

Copy the files/directories in this pack to the root of your repo. Merge any existing `AGENTS.md` rules rather than overwriting your own. If you already have the previous `orchestrator.py`, this version replaces it to include the real ThinkMedia SRS brief and a strict test gate.

Expected files:

```text
my-existing-repo/
├── AGENTS.md                         # ThinkMedia agent rules
├── orchestrator.py                   # Codex CLI supervisor
├── thinkmedia_phases.py              # five-phase auto-sequencing wrapper
├── verify.sh                         # replace/adapt for your real test setup
├── docs/
│   ├── THINKMEDIA_AGENT_BRIEF.md      # condensed SRS / FR/NFR / wireframes
│   └── THINKMEDIA_PHASES.md           # phased Gemini and DeepSeek tasks
└── [your existing frontend, backend and other project files]
```

Add to `.gitignore`:

```gitignore
.orchestrator/
.venv/
```

**Optional**: Copy the original DOCX to `docs/Requirements Software Engineering.docx` for human reference. The manager already receives the concise Markdown requirements even if the DOCX is absent.

## 3. Configure the actual models and test command

```bash
export SOL_MODEL='gpt-6.1-sol'
export UI_MODEL='gemini-3.8-flash-medium'
export BACKEND_MODEL='your-provider/your-deepseek-v4.1-flash-model-id'
export COOLDOWN_SECONDS=18000
export VERIFY_COMMAND='bash verify.sh'
```

Use `opencode models` to obtain the exact DeepSeek provider/model ID; the placeholder above is deliberately not a claim about your provider's naming.

Test each account interactively and confirm access to the requested model before running the orchestrator. Do not grant broad unattended shell permissions just to get past approval prompts. Give each tool narrowly scoped working-directory permissions and deny access to `.env` and secrets.

Run unit smoke tests (they mock CLI execution, so use no model tokens):

```bash
python3 -m unittest -v test_orchestrator.py test_phase_runner.py
```

## 4. Run the full project in stages

```bash
python3 thinkmedia_phases.py start
```

This runs five consecutive phases: foundation, OJT marketplace, learning + assistant, recommender, evaluation/QA. **Within each phase**, Gemini and DeepSeek work concurrently in the same repository on non-overlapping files. Sol plans the phase and reviews combined results. The next phase only starts after Sol approves a successful actual build/test verification. There is no fixed guarantee it will complete without human intervention—missing credentials, permissions, ambiguous product decisions and failed security tests should stop it.

Inspect:

```bash
python3 thinkmedia_phases.py status
python3 orchestrator.py status
ls -lah .orchestrator/logs/
```

Resume after a process interruption:

```bash
python3 thinkmedia_phases.py resume
```

A recognized *temporary quota error* pauses that agent for five hours by default while the main process stays alive; unrelated work can continue. A **Codex quota error** in a Sol planning/review turn also pauses planning/review. A monthly limit, insufficient credits, expired authentication or context overflow requires a different fix; this starter cannot guarantee provider quota restoration after five hours.

**Important:** A terminal/process exit, sleep, or WSL shutdown stops automatic timers. Run within `tmux`, a persistent Linux systemd user service, or an always-on VPS if you require unattended continuation. A VPS is not a way to bypass provider limits.

## 5. Testing, review and safe operation

`VERIFY_COMMAND='bash verify.sh'` is a basic detection-based gate that attempts a React build and Python tests when present. You **must** customize `verify.sh` to your actual repo: root vs `frontend/`, `backend/`, whether pytest runs from root, and whether integration tests require a local database. No build/tests means the workflow will not advance.

The previous supervisor asks workers to respect disjoint paths in one repo but does **not** enforce these paths via filesystem isolation. Review `git diff`, and use a throwaway branch and test database with no production secrets. If you need hard enforced file ownership, add OS sandbox permissions or use worktrees (still one Git repository) later.

Do not assume the AI-assistant provider is connected just because coding agents have model access. For a real demonstration you need a separately configured application AI provider, controlled request quotas, and approved reference content.

### Official CLIs

- Codex: https://learn.chatgpt.com/docs/cli/reference
- Antigravity headless: https://antigravity.google/docs/cli/headless/
- OpenCode: https://dev.opencode.ai/v2/docs/cli/commands/

### Skills

- Intent: https://github.com/ghaida/intent
- Impeccable: https://github.com/pbakaus/impeccable
