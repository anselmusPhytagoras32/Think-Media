#!/usr/bin/env python3
"""Simple prompt interface for the one-repo coding team."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
SUPERVISOR = ROOT / '.ai-team' / 'orchestrator.py'
STAGES = ROOT / '.ai-team' / 'stages.py'
RUN = ROOT / '.orchestrator'


def dispatch(args: list[str]) -> int:
    return subprocess.run([sys.executable, str(SUPERVISOR), *args], cwd=ROOT).returncode


def phases(args: list[str]) -> int:
    return subprocess.run([sys.executable, str(STAGES), *args], cwd=ROOT).returncode


def status():
    for filename in ('thinkmedia-progress.json', 'state.json'):
        p = RUN / filename
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding='utf-8'))
                if filename == 'state.json':
                    data = {k: data.get(k) for k in ('phase', 'request', 'workers', 'review', 'verification')}
                print(f'\n--- {filename} ---\n{json.dumps(data, indent=2, ensure_ascii=False)[:12000]}')
            except Exception as error:
                print(f'Could not inspect {p}: {error}')
        else:
            print(f'{filename}: not started')


def doctor():
    import importlib.util
    print('Working repository:', ROOT)
    for name in ('git', 'python3', 'codex', 'agy', 'opencode', 'node', 'npx'):
        print(f'{name:<10} {shutil.which(name) or "MISSING"}')
    print('Configuration:', 'installed' if (ROOT / '.ai-team/settings.env').exists() else 'run bash setup-team.sh')
    for key in ('SOL_MODEL', 'UI_MODEL', 'BACKEND_MODEL'):
        print(f'{key}: {os.getenv(key, "NOT CONFIGURED")}')
    skill_paths = [ROOT / '.agent/skills', ROOT / '.agents/skills']
    for path in skill_paths:
        skills = list(path.rglob('SKILL.md')) if path.exists() else []
        print(f'{path.relative_to(ROOT)}: {len(skills)} skills')
    print('Test script:', 'OK' if (ROOT / '.ai-team/verify.sh').is_file() else 'MISSING')
    print('Codex auth: run `codex login status` to check')
    print('Antigravity auth: run `agy` if not authenticated')
    print('OpenCode auth: run `opencode auth list` to check')


def logs():
    folder = RUN / 'logs'
    if not folder.exists():
        print('No logs yet.')
        return
    files = sorted((p for p in folder.iterdir() if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[:12]:
        print(f'{p.relative_to(ROOT)} ({p.stat().st_size} bytes)')


def run_goal(goal: str):
    active = RUN / 'state.json'
    if active.exists():
        state = json.loads(active.read_text())
        if state.get('phase') not in ('complete',):
            print('An earlier run is still unfinished. Use /status and /resume before a new prompt.')
            return 2
    if (RUN / 'thinkmedia-progress.json').exists():
        progress = json.loads((RUN / 'thinkmedia-progress.json').read_text())
        if progress.get('status') != 'complete':
            print('The full SRS build is still unfinished. Use /resume or inspect /status.')
            return 2
    return dispatch(['start', goal])


def start_background(arguments: list[str]):
    if not arguments:
        print('Usage: ./team background build   OR   ./team background "your feature prompt"')
        return 2
    RUN.mkdir(exist_ok=True)
    log = RUN / 'background.log'
    with log.open('a', encoding='utf-8') as fp:
        fp.write(f'\n=== START {time.ctime()} ===\n')
        fp.flush()
        command = [str(ROOT / 'team'), *(['build'] if arguments[0] == 'build' else [' '.join(arguments)])]
        # Child processes can survive a closed terminal, but NOT power-off or WSL shutdown.
        proc = subprocess.Popen(command, cwd=ROOT, stdout=fp, stderr=subprocess.STDOUT,
                                start_new_session=True, stdin=subprocess.DEVNULL)
    print(f'Background process PID: {proc.pid}. Logs: .orchestrator/background.log')
    print('Run ./team status to see progress. WSL must remain running.')
    return 0


def run_command(arguments: list[str]):
    if not arguments:
        return repl()
    cmd, *other = arguments
    if cmd in ('-h','--help','help','/help'):
        print('''ThinkMedia Agent Team
  ./team                         interactive prompt
  ./team "Build profile editing"   prompt Sol, Gemini, DeepSeek
  ./team build                   all five SRS development phases
  ./team background build        start SRS build in background
  ./team resume                  resume an interrupted build/task
  ./team status                  show saved agent progress
  ./team retry ui|backend        retry a failed worker
  ./team doctor                  check local CLI setup
  ./team model                   change DeepSeek model without reinstalling tools/skills
  ./team logs                    list log files
  ./team watch                   live read-only dashboard of all 3 agents

Inside ./team interactive mode: /build, /model, /watch, /status, /resume, /doctor, /logs, /quit.
Keep WSL running for unattended five-hour retries. Never paste API keys into prompts.''')
        return 0
    if cmd in ('model','/model'):
        return subprocess.run([sys.executable, str(ROOT / '.ai-team' / 'model_picker.py')], cwd=ROOT).returncode
    if cmd in ('status','/status'):
        status(); return 0
    if cmd in ('doctor','/doctor'):
        doctor(); return 0
    if cmd in ('logs','/logs'):
        logs(); return 0
    if cmd in ('watch','/watch'):
        return subprocess.run([sys.executable, str(ROOT / '.ai-team' / 'monitor.py')], cwd=ROOT).returncode
    if cmd in ('build','/build'):
        p = RUN / 'thinkmedia-progress.json'
        if p.exists():
            data = json.loads(p.read_text())
            if data.get('status') != 'complete':
                print('A staged run exists. Resuming it rather than starting over.')
                return phases(['resume'])
            print('Full build already completed. Use natural language prompts for improvements.')
            return 0
        return phases(['start'])
    if cmd in ('resume','/resume'):
        p = RUN / 'thinkmedia-progress.json'
        if p.exists() and json.loads(p.read_text()).get('status') != 'complete':
            return phases(['resume'])
        return dispatch(['resume'])
    if cmd in ('retry','/retry'):
        if len(other) != 1 or other[0] not in ('ui','backend'):
            print('Usage: ./team retry ui|backend'); return 2
        return dispatch(['retry', other[0]])
    if cmd == 'background':
        return start_background(other)
    return run_goal(' '.join(arguments))


def repl():
    print('ThinkMedia team: Sol (Codex) + Gemini (Antigravity) + DeepSeek (OpenCode).')
    print('Type what you want built, /build for the full SRS, or /help for commands.')
    while True:
        try:
            prompt = input('\nThinkMedia > ').strip()
        except (KeyboardInterrupt, EOFError):
            print(); return 0
        if not prompt:
            continue
        if prompt in ('/exit', '/quit', 'exit', 'quit'):
            return 0
        try:
            run_command([prompt] if prompt.startswith('/') else [prompt])
        except KeyboardInterrupt:
            print('\nInterrupted. Type /resume to continue unfinished work.')


if __name__ == '__main__':
    sys.exit(run_command(sys.argv[1:]))
