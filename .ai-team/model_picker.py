#!/usr/bin/env python3
"""Pick the backend model from OpenCode without rerunning setup or npm."""
from __future__ import annotations
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / '.ai-team' / 'settings.env'
DEFAULTS = {
    'SOL_MODEL': 'gpt-6.1-sol',
    'UI_MODEL': 'gemini-3.8-flash-medium',
    'COOLDOWN_SECONDS': '18000',
    'OPENCODE_AUTO': '1',
    'VERIFY_COMMAND': 'bash .ai-team/verify.sh',
}


def existing_backend() -> str | None:
    if not CONFIG.is_file():
        return None
    for line in CONFIG.read_text(encoding='utf-8').splitlines():
        if line.startswith('export BACKEND_MODEL='):
            try:
                parsed = shlex.split(line)
                if len(parsed) == 2 and parsed[0] == 'export' and '=' in parsed[1]:
                    return parsed[1].split('=', 1)[1]
            except ValueError:
                pass
    return None


def store_model(model: str) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    lines = CONFIG.read_text(encoding='utf-8').splitlines() if CONFIG.exists() else []
    update = 'export BACKEND_MODEL=' + shlex.quote(model)
    replaced = False
    for i, line in enumerate(lines):
        if line.startswith('export BACKEND_MODEL='):
            lines[i] = update
            replaced = True
            break
    if not replaced:
        if not lines:
            lines += ['export ' + k + '=' + shlex.quote(v) for k, v in DEFAULTS.items()]
        lines.append(update)
    # Restrict file permissions even when setup was interrupted.
    CONFIG.touch(mode=0o600, exist_ok=True)
    CONFIG.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    CONFIG.chmod(0o600)


def main() -> int:
    print('Checking OpenCode models (no skills or CLIs will be installed)...')
    try:
        out = subprocess.run(['opencode','models'], capture_output=True, text=True, timeout=90)
    except FileNotFoundError:
        print('OpenCode not found. Install it once with setup-team.sh first.',file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print('OpenCode models timed out; check your network/auth.',file=sys.stderr)
        return 1
    if out.returncode:
        print((out.stderr or out.stdout).strip()[:2000],file=sys.stderr)
        print('Connect provider with: opencode auth login',file=sys.stderr)
        return out.returncode
    # Model IDs are provider/model. Avoid listing arbitrary diagnostics.
    all_models = [line.strip() for line in out.stdout.splitlines() if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.:/-]+', line.strip())]
    matches = [m for m in all_models if 'deepseek' in m.lower() and ('flash' in m.lower() or re.search(r'4[.-]?1',m))]
    if not matches:
        print('No DeepSeek Flash/V4.1 entry found in `opencode models`.')
        print('Run `opencode auth login` to connect the provider, then `./team model` again.')
        return 2
    print('Available DeepSeek candidates:')
    for i, model in enumerate(matches, 1):
        print(f'  {i}. {model}')
    prior = existing_backend()
    default = prior if prior in matches else matches[0]
    while True:
        try:
            value = input(f'Select number or paste exact model ID [{default}]: ').strip()
        except EOFError:
            print('No input received; model unchanged.')
            return 2
        chosen = default if not value else (matches[int(value)-1] if value.isdigit() and 1<=int(value)<=len(matches) else value)
        if chosen in all_models and 'deepseek' in chosen.lower():
            break
        print('Choose one of the DeepSeek model IDs printed by `opencode models`.')
    store_model(chosen)
    print(f'Updated .ai-team/settings.env: BACKEND_MODEL={chosen}')
    print('Ready. Run ./team doctor or ./team. You do NOT need setup-team.sh again.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
