#!/usr/bin/env python3
"""Run ThinkMedia's SRS-driven phases over the existing Codex CLI supervisor.

Does not use OpenAI APIs. Stores per-phase progress under .orchestrator/.
Requires orchestrator.py and the docs in this pack.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path.cwd().resolve()
ORCH_DIR = ROOT / '.orchestrator'
PROGRESS = ORCH_DIR / 'thinkmedia-progress.json'
PHASES = [
    ('foundation',
     'THINKMEDIA PHASE 1 — FOUNDATION. Implement B01 and company verification foundation. '
     'Meet FR01–FR02, relevant FR11, NFR02/03/04/06 and W01. '
     'Auth, profiles, roles, RBAC and admin verification with audited changes. '
     'Gemini implements role-specific responsive login/profile screens and an admin verification UI, '
     'following Intent and Impeccable. DeepSeek implements modular FastAPI/PostgreSQL schema, '
     'auth, server role checks, company verification and negative security tests. '
     'Read and follow AGENTS.md, docs/THINKMEDIA_AGENT_BRIEF.md, '
     'and the Phase 1 detailed checklist in docs/THINKMEDIA_PHASES.md. '
     'Analyze the EXISTING repo first. Prepare a shared API contract before concurrent edits.'),
    ('ojt-marketplace',
     'THINKMEDIA PHASE 2 — OJT MARKETPLACE. Implement B02–B04, FR04–FR07, W03–W05. '
     'Verified company listing ownership, Published/Closed workflow, student browse/search, '
     'one application per student/listing, private validated attachments, transactional receipt, '
     'student status tracking and company owner-only status changes/audit. '
     'Gemini does UI via Intent and Impeccable; DeepSeek does APIs, migrations, authorization and tests. '
     'Read AGENTS.md, docs/THINKMEDIA_AGENT_BRIEF.md and Phase 2 in docs/THINKMEDIA_PHASES.md; '
     'honor API contracts and only edit assigned file paths.'),
    ('learning-assistant',
     'THINKMEDIA PHASE 3 — LEARNING AND AI. Implement B05/B07/B09, FR03/FR10/FR11 and W02/W07. '
     'Gemini: approved-content feed, filters, saves, reactions, quizzes and polished grounded assistant UI '
     'with Intent and Impeccable. DeepSeek: publication/moderation, quiz scoring, interactions, '
     'approved-content RAG/retrieval, server-only LLM adapter with a safe mock mode, clear citations, '
     'no access to private applications, graceful provider outages. '
     'Read AGENTS.md, docs/THINKMEDIA_AGENT_BRIEF.md and Phase 3 in docs/THINKMEDIA_PHASES.md.'),
    ('recommendations',
     'THINKMEDIA PHASE 4 — RECOMMENDATIONS. Implement B06/B08, FR08–FR09 and W06. '
     'Gemini: recommendation panels, explanations, optional feedback UI, fallback state and accessible design '
     'using Intent and Impeccable. DeepSeek: profile/content-based candidate ranking, eligible-only filter, '
     'real interaction event capture, collaborative component only when sufficient data, alpha validation, '
     'cold-start handling and deterministic tests. '
     'Read AGENTS.md, docs/THINKMEDIA_AGENT_BRIEF.md and Phase 4 in docs/THINKMEDIA_PHASES.md.'),
    ('evaluation-qa',
     'THINKMEDIA PHASE 5 — EVALUATION AND QA. Audit FR01–FR12, NFR01–NFR11 and all W01–W08. '
     'Gemini: Intent/Impeccable-responsive + accessibility tests and fixes at 360px/mobile/desktop. '
     'DeepSeek: cross-tenant security, transaction rollback, benchmarking p95 at 20 concurrent users, '
     'real-data MAE/RMSE/baseline/k-fold evaluation scripts, BERTScore and CSAT evaluation harness, '
     'documented test conditions, sample counts and honest unmeasured statuses. '
     'No fabricated evidence; no production deploy. '
     'Read AGENTS.md, docs/THINKMEDIA_AGENT_BRIEF.md and Phase 5 in docs/THINKMEDIA_PHASES.md.'),
]


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    tmp.replace(path)


def read_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None


def archive_stage(index: int, slug: str) -> None:
    target = ORCH_DIR / 'history' / f'{index + 1:02d}-{slug}'
    target.mkdir(parents=True, exist_ok=True)
    for name in ['state.json', 'plan.md', 'sol-plan-result.json', 'sol-review-result.json']:
        p = ORCH_DIR / name
        if p.is_file(): shutil.copy2(p, target / name)
    logs = ORCH_DIR / 'logs'
    if logs.exists():
        shutil.copytree(logs, target / 'logs', dirs_exist_ok=True)


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ('start', 'resume', 'status'):
        print('Usage: python3 thinkmedia_phases.py start|resume|status')
        return 2
    for required in ('AGENTS.md', 'docs/THINKMEDIA_AGENT_BRIEF.md',
                     'docs/THINKMEDIA_PHASES.md', 'orchestrator.py'):
        if not (ROOT / required).exists():
            print(f'Missing required project file: {required}', file=sys.stderr)
            return 2
    action = sys.argv[1]
    if action == 'status':
        print(json.dumps(read_json(PROGRESS) or {'status': 'not started'}, indent=2))
        return 0
    if action == 'start':
        if PROGRESS.exists():
            print('A ThinkMedia workflow exists; run `resume` instead.', file=sys.stderr)
            return 2
        existing = read_json(ORCH_DIR / 'state.json')
        if existing and existing.get('phase') not in ('complete',):
            print('An unrelated supervisor run is unfinished. Finish it before starting.', file=sys.stderr)
            return 2
        progress = {'next_phase_index': 0, 'history': [], 'status': 'running'}
        write_json(PROGRESS, progress)
    else:
        progress = read_json(PROGRESS)
        if not progress:
            print('No ThinkMedia workflow; run `start` first.', file=sys.stderr)
            return 2
    while progress['next_phase_index'] < len(PHASES):
        i = progress['next_phase_index']
        slug, prompt = PHASES[i]
        state = read_json(ORCH_DIR / 'state.json')
        # The supervisor tracks its own current plan, cooldowns, and sessions.
        # A completed phase is only archived/advanced after review approval.
        if (state and state.get('phase') == 'complete'
                and state.get('review', {}).get('approved')
                and state.get('request') == prompt):
            if progress.get('active_slug') == slug:
                archive_stage(i, slug)
                progress['history'].append({'phase': slug, 'approved': True,
                    'completed_at': datetime.now(timezone.utc).isoformat()})
                progress['next_phase_index'] += 1
                progress.pop('active_slug', None)
                write_json(PROGRESS, progress)
                continue
        if progress.get('active_slug') == slug and state and state.get('request') == prompt:
            if state.get('phase') == 'needs_attention':
                print(f'Phase {i + 1} requires attention; inspect .orchestrator/state.json and logs.', file=sys.stderr)
                return 1
            cmd = [sys.executable, 'orchestrator.py', 'resume']
        else:
            progress['active_slug'] = slug
            write_json(PROGRESS, progress)
            cmd = [sys.executable, 'orchestrator.py', 'start', prompt]
        print(f'\n[ThinkMedia] Phase {i + 1}/{len(PHASES)}: {slug}', flush=True)
        result = subprocess.run(cmd, cwd=ROOT)
        state = read_json(ORCH_DIR / 'state.json')
        if result.returncode or not state or state.get('phase') != 'complete' or not state.get('review', {}).get('approved'):
            print('Stopped. Inspect status and logs; fix blockers, then use `python3 thinkmedia_phases.py resume`.', file=sys.stderr)
            return 1
        # The next iteration performs archive+advancement and starts next phase.
    progress['status'] = 'complete'
    write_json(PROGRESS, progress)
    print('\n[ThinkMedia] All five phases approved and archived.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
