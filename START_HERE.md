# ThinkMedia: ready-to-run local multi-agent team

This package is designed to be **extracted into your existing Git repository**, not used as a new repository. Your application files are not replaced. It was built from the uploaded ThinkMedia SRS; a compact brief and a full extracted copy of the SRS are in `.ai-team/spec/`.

## What runs

- **Orchestrator**: GPT-6.1 Sol using **Codex CLI signed in with ChatGPT**; no OpenAI API key or Agents SDK.
- **UI worker**: Gemini 3.8 Flash via Antigravity CLI with installed **Intent + Impeccable** skills.
- **Backend worker**: DeepSeek V4.1 Flash via OpenCode CLI, with the **actual provider/model name chosen on your machine**.
- **Supervisor**: Python standard-library-only CLI calls. Parallel UI/backend execution in **one working tree**, disjoint paths by instruction, state in `.orchestrator/`, five-hour fallback cooldown for recognized temporary provider quota failures, stage-by-stage Sol review.

## Quick start — Debian/Ubuntu WSL

1. Download the ZIP, move it into the **root of your existing Git repository** (your project), and extract it. If `unzip` is missing, run `sudo apt install unzip`.

   ```bash
   cd /path/to/your/existing/thinkmedia-repo
   unzip ThinkMedia_One_Command_Agents.zip
   ```

2. Run the installer from the same directory:

   ```bash
   bash setup-team.sh
   ```

   The installer checks/installs the needed CLIs, asks you to complete Google/ChatGPT/DeepSeek sign-in if required, installs both design skills, asks for the exact DeepSeek model, saves a local settings file, and appends a short reference to your existing `AGENTS.md` (without deleting its contents). **Sign-in and provider access cannot be done for you remotely.** It may require browser actions.

3. Start the team and type a task:

   ```bash
   ./team
   ```

   Example prompt: `Implement student registration and login according to FR01 and FR02, with responsive polished UI and verified authorization tests.`

   Or type `/build` to attempt the **entire ThinkMedia SRS** in five stages, with separate UI/backend tasks inside each stage.

## Commands

```bash
./team                         # interactive prompt
./team "Improve the OJT portal" # one specific natural-language task
./team build                   # full SRS in five approved phases
./team background build        # full SRS detached; keep WSL running
./team status                  # state + session and cooldown info
./team resume                  # resume if supervisor was interrupted
./team retry ui                # after fixing a UI worker failure
./team retry backend           # after fixing a backend worker failure
./team logs                    # recent log files
./team doctor                  # CLI and skill checks
```

Background logs: `tail -f .orchestrator/background.log`. Worker logs: `.orchestrator/logs/`. The process pauses a worker for 18,000 seconds on a recognized temporary limit, resumes saved Antigravity/OpenCode sessions when IDs are available, and lets unaffected work continue. **A sleeping/powered-off PC, stopped WSL environment, bad credentials, weekly limit, or insufficient funds cannot be autonomously repaired.** `./team resume` continues from the persistent state after restarting.

## Safety, tests, and realistic limits

- Run on a new Git branch and commit existing work first. The installer does not create commits or force Git changes. It adds `AGENTS.md`, `.gitignore` entries, skill files, and this agent harness; `npx` installers may add more project-local skill files. Review with `git status`.
- This is **one repository** with concurrent workers. Disjoint file ownership is requested and validated in Sol's plan, but **not protected by an OS filesystem boundary**. Use it on a backed-up branch and inspect diffs. If hard path enforcement becomes necessary, isolate the agents using worktrees (same Git repository) or filesystem sandboxes.
- Antigravity uses `--mode=auto` sandboxed automation where supported. On WSL kernels without the sandbox, approval-required tools may be soft-denied; the harness flags that rather than claiming success. OpenCode runs with `--auto` for tasks; do not use this on repositories containing production secrets or infrastructure credentials.
- Sol plans the architecture and API contract before dispatching the two workers. Agent outputs must be independently tested. `.ai-team/verify.sh` auto-detects common React builds and Python tests. It rejects the stage if no tests or build exist. For a nonstandard layout, modify `.ai-team/verify.sh` to match real scripts.
- API runtime AI chatbot in ThinkMedia requires its own provider key/budget. Codex/Antigravity/OpenCode subscriptions do not automatically cover the **application's** AI service.
- Real deployment and operations (pushing commits, secrets, live migrations, production data, real emails) require your approval. Research evaluation scores must come from actual data and cannot be fabricated.
- No guarantee that an autonomous five-stage build will finish without intervention; accounts, tools, permission modes and tests must work. This pack is verified using local mocked CLI tests, not your real authenticated project.

## Local harness self-test (no model tokens)

```bash
python3 -m unittest discover -s .ai-team/tests -p 'test_*.py' -v
```

## Official help

- Codex CLI: https://learn.chatgpt.com/docs/cli
- Antigravity: https://antigravity.google/docs/cli/headless/
- OpenCode: https://dev.opencode.ai/v2/docs/cli/commands/
- Intent: https://github.com/ghaida/intent
- Impeccable: https://github.com/pbakaus/impeccable
