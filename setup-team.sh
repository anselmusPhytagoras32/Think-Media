#!/usr/bin/env bash
# Idempotent WSL/Linux setup. Run from your existing repository root.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
ROOT="$(pwd -P)"

say() { printf '\n==> %s\n' "$*"; }
die() { echo "SETUP STOPPED: $*" >&2; exit 1; }

[[ -d .ai-team && -f .ai-team/orchestrator.py ]] || die 'Extract this entire ZIP to your Git repository root first.'
command -v git >/dev/null 2>&1 || die 'Install git first (e.g. sudo apt install git).'
command -v python3 >/dev/null 2>&1 || die 'Install Python 3.10+ first (e.g. sudo apt install python3).'
command -v curl >/dev/null 2>&1 || die 'Install curl first (e.g. sudo apt install curl).'
[[ "$(git rev-parse --show-toplevel 2>/dev/null)" == "$ROOT" ]] || die 'Run from the ROOT of your existing Git repository.'
python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit('Python 3.10+ required')
PY

export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$HOME/.opencode/bin:$HOME/.codex/bin:$PATH"

say 'Check Node.js 22 (required by modern skills installer)'
if ! command -v node >/dev/null 2>&1 || ! command -v npx >/dev/null 2>&1 || ! node -e 'let [a,b]=process.versions.node.split(".").map(Number);process.exit(a>22||(a===22&&b>=20)?0:1)' 2>/dev/null; then
  echo 'Installing Node 22 via nvm into your home directory.'
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  if [[ ! -s "$NVM_DIR/nvm.sh" ]]; then
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
  fi
  # shellcheck disable=SC1090
  source "$NVM_DIR/nvm.sh"
  nvm install 22
  nvm use 22
fi

say 'Install the three CLIs only when missing'
if ! command -v codex >/dev/null 2>&1; then
  echo 'Installing official Codex CLI...'
  curl -fsSL https://chatgpt.com/codex/install.sh | sh
fi
if ! command -v agy >/dev/null 2>&1; then
  echo 'Installing official Antigravity CLI...'
  curl -fsSL https://antigravity.google/cli/install.sh | bash
fi
if ! command -v opencode >/dev/null 2>&1; then
  echo 'Installing OpenCode v2...'
  curl -fsSL https://opencode.ai/v2/install | bash
fi
hash -r
for tool in codex agy opencode; do
  command -v "$tool" >/dev/null 2>&1 || die "$tool installed but is not in PATH. Open a new WSL terminal and rerun setup."
done

say 'Ensure Codex is signed in with your ChatGPT subscription'
if ! codex login status; then
  codex login || die 'Codex sign-in was not completed. Run codex login and rerun setup.'
fi

say 'Ensure Antigravity login has been initialized'
echo 'Antigravity model list:'
agy models | head -30 || true
if ! agy -p 'Reply with exactly READY. Do not edit any files.' --model gemini-3.8-flash-medium --output-format json --print-timeout 90s > .ai-team/agy-login-check.json 2> .ai-team/agy-login-check.err; then
  echo 'Antigravity may need sign-in. Complete the interactive steps below and exit.'
  agy || die 'Antigravity sign-in failed. Run agy and rerun setup.'
fi

say 'Install project-local Antigravity design skills'
# Install Impeccable into .agent/ and Intent into .agents/skills, where agy discovers it.
npx --yes impeccable install --providers=antigravity --scope=project || die 'Impeccable install failed; run npx impeccable install and select Google Antigravity and Project.'
npx --yes skills add ghaida/intent --all --agent antigravity-cli --yes || die 'Intent installation failed; run npx skills add ghaida/intent --all and select Antigravity CLI.'

if ! find .agent/skills .agents/skills -type f -name SKILL.md 2>/dev/null | grep -q .; then
  die 'No SKILL.md found after installation. Re-run the skill installers and verify their target.'
fi

echo 'Installed skill definitions:'
find .agent/skills .agents/skills -type f -name SKILL.md 2>/dev/null | head -25 || true

say 'Select the DeepSeek Flash model available in OpenCode'
echo 'Checking model catalog...'
MODELS="$(opencode models 2>&1 || true)"
CANDIDATES="$(printf '%s\n' "$MODELS" | grep -iE 'deepseek.*(flash|4\.1)' | grep -E '^[[:alnum:]_.-]+/[[:alnum:]_.:/-]+' || true)"
if [[ -z "$CANDIDATES" ]]; then
  echo 'No DeepSeek Flash model is listed. Connect a suitable OpenCode provider:'
  echo '  opencode auth login'
  echo 'Then run: opencode models'
  echo 'And rerun this setup command.'
  exit 2
fi
printf '%s\n' "$CANDIDATES"
RECOMMENDED="$(printf '%s\n' "$CANDIDATES" | grep -iE '4[.-]?1.*flash|flash.*4[.-]?1' | head -1 || true)"
if [[ -z "$RECOMMENDED" ]]; then
  RECOMMENDED="$(printf '%s\n' "$CANDIDATES" | head -1)"
fi
if [[ -f .ai-team/settings.env ]]; then
  # shellcheck disable=SC1091
  source .ai-team/settings.env
fi
DEFAULT_BACKEND="${BACKEND_MODEL:-$RECOMMENDED}"
read -r -p "Exact OpenCode DeepSeek model ID [$DEFAULT_BACKEND]: " CHOSEN_MODEL || true
CHOSEN_MODEL="${CHOSEN_MODEL:-$DEFAULT_BACKEND}"
[[ "$CHOSEN_MODEL" == */* ]] || die 'Model ID must be provider/model from opencode models.'
if ! printf '%s\n' "$MODELS" | grep -Fxq "$CHOSEN_MODEL"; then
  echo "Warning: '$CHOSEN_MODEL' not found as an exact model ID in catalog."
  read -r -p 'Use this ID anyway? [y/N]: ' CONFIRM || true
  [[ "$CONFIRM" =~ ^[yY]$ ]] || die 'Run setup again and select an exact listed model.'
fi

say 'Write local settings (no OpenAI API key required)'
{
  printf 'export SOL_MODEL=%q\n' "${SOL_MODEL:-gpt-6.1-sol}"
  printf 'export UI_MODEL=%q\n' "${UI_MODEL:-gemini-3.8-flash-medium}"
  printf 'export BACKEND_MODEL=%q\n' "$CHOSEN_MODEL"
  printf 'export COOLDOWN_SECONDS=%q\n' "18000"
  printf 'export OPENCODE_AUTO=%q\n' "1"
  printf 'export VERIFY_COMMAND=%q\n' "bash .ai-team/verify.sh"
  printf 'export PATH=%q:$PATH\n' "$HOME/.local/bin:$HOME/.opencode/bin:$HOME/.codex/bin"
} > .ai-team/settings.env
chmod 600 .ai-team/settings.env

say 'Register project instructions without overwriting existing AGENTS.md'
if [[ ! -f AGENTS.md ]]; then touch AGENTS.md; fi
if ! grep -Fq '<!-- THINKMEDIA_TEAM_INSTRUCTIONS_START -->' AGENTS.md; then
cat >> AGENTS.md <<'EOF'

<!-- THINKMEDIA_TEAM_INSTRUCTIONS_START -->
# ThinkMedia coding team
Before planning or modifying this repository, read `.ai-team/AGENT_RULES.md` and
`.ai-team/spec/THINKMEDIA_AGENT_BRIEF.md` plus the current phase in
`.ai-team/spec/THINKMEDIA_PHASES.md`.
Use the SRS acceptance criteria, keep frontend and backend write paths separate,
and require real tests and evidence. Do not deploy, push, or expose secrets.
<!-- THINKMEDIA_TEAM_INSTRUCTIONS_END -->
EOF
fi

say 'Protect runtime state from Git'
for ignore in '.orchestrator/' '.ai-team/settings.env' '.ai-team/agy-login-check.json' '.ai-team/agy-login-check.err'; do
  if [[ ! -f .gitignore ]] || ! grep -Fxq "$ignore" .gitignore; then printf '%s\n' "$ignore" >> .gitignore; fi
done

chmod +x ./team .ai-team/verify.sh
say 'SETUP FINISHED'
echo "Project: $ROOT"
echo 'Use ./team doctor to check the setup.'
echo 'Use ./team to enter a natural-language prompt, or ./team build for the complete ThinkMedia SRS.'
echo 'If you want unattended execution, use ./team background build and keep WSL running.'
echo 'If a CLI reports permission denied, inspect its log and configure limited permissions (never blanket unsafe access).'
