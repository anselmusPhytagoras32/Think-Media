"""Smoke test staging without requiring Codex, Gemini, or DeepSeek accounts."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

PACK = Path(__file__).resolve().parent


class PhaseRunnerTests(unittest.TestCase):
    def test_progression_and_archival(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ['thinkmedia_phases.py', 'AGENTS.md',
                        'docs/THINKMEDIA_AGENT_BRIEF.md', 'docs/THINKMEDIA_PHASES.md']:
                out = root / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PACK / rel, out)
            # Substitute stub supervisor: checks it receives "start" per phase and
            # writes a success state with request; no model calls or repo edits.
            (root / 'orchestrator.py').write_text('''
import json, sys
from pathlib import Path
state_path = Path('.orchestrator/state.json')
if sys.argv[1] != 'start':
    raise SystemExit('Expected start for each fresh phase')
state_path.parent.mkdir(exist_ok=True)
state_path.write_text(json.dumps({
    'request': sys.argv[2], 'phase':'complete',
    'review': {'approved': True, 'summary':'smoke mock'}
}))
Path('.orchestrator/plan.md').write_text('mock plan')
''', encoding='utf-8')
            result = subprocess.run([sys.executable, 'thinkmedia_phases.py', 'start'],
                                    cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            p = json.loads((root / '.orchestrator/thinkmedia-progress.json').read_text())
            self.assertEqual(p['status'], 'complete')
            self.assertEqual(len(p['history']), 5)
            self.assertEqual(p['next_phase_index'], 5)
            self.assertTrue((root / '.orchestrator/history/05-evaluation-qa/plan.md').exists())

    def test_no_advance_on_stale_previous_phase_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ['thinkmedia_phases.py', 'AGENTS.md',
                        'docs/THINKMEDIA_AGENT_BRIEF.md', 'docs/THINKMEDIA_PHASES.md']:
                dst = root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PACK / rel, dst)
            (root / 'orchestrator.py').write_text('raise SystemExit("fail before state")\n')
            state = root / '.orchestrator'
            state.mkdir()
            (state / 'state.json').write_text(json.dumps({
                'request': 'previous unrelated success', 'phase':'complete',
                'review':{'approved':True}
            }))
            (state / 'thinkmedia-progress.json').write_text(json.dumps({
                'next_phase_index':0, 'active_slug':'foundation', 'history':[], 'status':'running'
            }))
            result = subprocess.run([sys.executable, 'thinkmedia_phases.py', 'resume'],
                                    cwd=root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            p = json.loads((state / 'thinkmedia-progress.json').read_text())
            self.assertEqual(p['next_phase_index'], 0)

if __name__ == '__main__':
    unittest.main()
