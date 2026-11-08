#!/usr/bin/env python3
"""Read-only monitor for the ThinkMedia Codex/Antigravity/OpenCode supervisor.

Usage: ./team watch
Run in another terminal; Ctrl+C only stops this monitor, not the agents.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import time
from datetime import datetime

from orchestrator import brief_event

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / '.orchestrator'
LOGS = RUN / 'logs'
ROLES = ('sol', 'ui', 'backend')
LABELS = {'sol': 'Sol / Codex', 'ui': 'Gemini / Antigravity', 'backend': 'DeepSeek / OpenCode'}


def load(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def newest_log(role):
    if not LOGS.exists():
        return None
    prefix = {'sol': 'sol-', 'ui': 'ui-', 'backend': 'backend-'}[role]
    files = [p for p in LOGS.glob(prefix + '*.log') if p.is_file()]
    return max(files, key=lambda p: p.stat().st_mtime, default=None)


def safe_preview(message, limit=150):
    cleaned = ' '.join(str(message).split())
    return cleaned[:limit] + ('…' if len(cleaned) > limit else '')


def activity(path, role, lines=5):
    if not path:
        return ['No output log yet.']
    try:
        # Read at most the tail 120 KB, even for long-running agents.
        with path.open('rb') as f:
            f.seek(0, 2)
            total = f.tell()
            f.seek(max(0, total - 120_000))
            raw = f.read().decode('utf-8', errors='replace')
    except OSError as exc:
        return [f'Log unavailable: {exc}']
    summary = []
    for line in raw.splitlines():
        if line.startswith('[stdout] '):
            try:
                evt = json.loads(line[9:])
            except ValueError:
                continue
            title = brief_event(role, evt)
            if title and (not summary or title != summary[-1]):
                summary.append(safe_preview(title))
        elif line.startswith('[stderr] '):
            body = safe_preview(line[9:])
            if body:
                summary.append('stderr: ' + body)
        elif line.startswith('[stdout]') or line.startswith('[stderr]'):
            continue
    return summary[-lines:] or ['Log exists, but no displayable events yet.']


def role_status(state, role):
    phase = state.get('phase', '')
    if role == 'sol':
        if phase == 'planning':
            return 'PLANNING', state.get('sol_pid')
        if phase == 'review':
            return 'REVIEWING', state.get('sol_pid')
        if phase == 'working':
            return 'WAITING FOR WORKERS', state.get('sol_pid')
        return phase.upper() if phase else 'NOT STARTED', state.get('sol_pid')
    worker = (state.get('workers') or {}).get(role, {})
    if not worker:
        return ('WAITING FOR SOL' if phase == 'planning' else 'NOT STARTED'), None
    stat = worker.get('status', 'unknown').upper()
    if stat == 'COOLDOWN':
        remaining = max(0, (worker.get('next_run') or 0) - time.time())
        stat += f' ({remaining/3600:.2f} h remaining)'
    if worker.get('attempt'):
        stat += f' / attempt {worker["attempt"]}'
    return stat, worker.get('pid')


def build_screen():
    progress = load(RUN / 'thinkmedia-progress.json')
    state = load(RUN / 'state.json')
    columns = shutil.get_terminal_size((100, 32)).columns
    bar = '─' * min(columns, 100)
    output = []
    output.append('THINKMEDIA — LIVE AGENT MONITOR')
    output.append(bar)
    active = progress.get('active_slug') or '—'
    index = progress.get('next_phase_index', 0)
    output.append(f'Project: {progress.get("status", "not started")}  |  Phase {index + 1}/5: {active}  |  Supervisor: {state.get("phase", "not started")}')
    output.append(f'Updated: {state.get("updated_at", "—")}  |  Now: {datetime.now().strftime("%H:%M:%S")}')
    output.append('This monitor is read-only. Ctrl+C closes it without stopping your agents.')
    for role in ROLES:
        status, pid = role_status(state, role)
        output.append('')
        output.append(bar)
        output.append(f'{LABELS[role]}  |  {status}' + (f'  |  PID {pid}' if pid else ''))
        path = newest_log(role)
        if path:
            output.append(f'Log: {path.relative_to(ROOT)}')
        for line in activity(path, role):
            output.append('  • ' + safe_preview(line, max(30, min(180, columns - 7))))
    output.append('')
    output.append(bar)
    output.append('Raw logs: ./team logs  |  Detailed saved state: ./team status  |  Refresh: 2 seconds')
    if state.get('phase') == 'planning' and newest_log('sol') is None:
        output.append('Note: a build started before the monitor patch will not have a live Codex log until planning ends.')
    return '\n'.join(output)


def main():
    if not sys.stdout.isatty():
        print(build_screen())
        return
    try:
        while True:
            sys.stdout.write('\033[2J\033[H' + build_screen() + '\n')
            sys.stdout.flush()
            time.sleep(2)
    except KeyboardInterrupt:
        print('\nMonitor closed; orchestration continues in the original terminal.')


if __name__ == '__main__':
    main()
