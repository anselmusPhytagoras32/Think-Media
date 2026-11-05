"""Unit/smoke tests for supervisor logic; do not call real providers."""
import asyncio
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import orchestrator as orch


class StarterTests(unittest.TestCase):
    def test_quota_classifier(self):
        self.assertTrue(orch.quota_error('API returned 429 rate limit exceeded'))
        self.assertFalse(orch.quota_error('Insufficient credits: billing balance exhausted'))
        self.assertFalse(orch.quota_error('maximum context length is too large'))

    def test_reject_overlapping_ownership(self):
        p = {'architecture':'a', 'api_contract':'b', 'ui_paths':['src'], 'backend_paths':['src/api'], 'ui_task':'x', 'backend_task':'y', 'suggested_verification':'z'}
        with self.assertRaises(ValueError):
            orch.validate_paths(p)

    def test_codex_planner_via_signed_in_cli_mock(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            root = tmp / 'repo'
            root.mkdir()
            bindir = tmp / 'bin'
            bindir.mkdir()
            exe = bindir / 'codex'
            exe.write_text(
                '#!/usr/bin/env python3\n'
                'import sys, json\n'
                'args=sys.argv\n'
                'assert args[1:3] == ["exec", "--json"]\n'
                'assert "--sandbox" in args and args[args.index("--sandbox")+1]=="read-only"\n'
                'result=args[args.index("--output-last-message")+1]\n'
                'data={"architecture":"ok","api_contract":"GET /test",'
                '"ui_paths":["frontend"],"backend_paths":["backend"],'
                '"ui_task":"UI","backend_task":"API","suggested_verification":"pytest"}\n'
                'open(result,"w").write(json.dumps(data))\n'
                'print(json.dumps({"type":"turn.completed"}))\n'
            )
            exe.chmod(0o755)
            with patch.object(orch, 'ROOT', root), patch.object(orch, 'DATA', root / '.orchestrator'), patch.object(orch, 'STATE_FILE', root / '.orchestrator/state.json'), patch.object(orch, 'LOGS', root / '.orchestrator/logs'), patch.dict(os.environ, {'PATH':f'{bindir}:'+os.environ['PATH']}):
                state = {'sol_cooldown_until': 0}
                result = asyncio.run(orch.sol_call(state, 'plan', orch.PLAN_SCHEMA, 'Plan the task'))
                self.assertEqual(result['ui_task'], 'UI')
                self.assertEqual(state['sol_attempt'], 1)
                self.assertEqual(state['sol_cooldown_until'], 0)
                self.assertTrue((root/'.orchestrator/sol-plan-result.json').exists())

    def test_codex_recovers_from_quota_error_without_api(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            root = tmp / 'repo'
            root.mkdir()
            bindir = tmp / 'bin'
            bindir.mkdir()
            exe = bindir / 'codex'
            exe.write_text(
                '#!/usr/bin/env python3\n'
                'import sys, json, pathlib\n'
                'args=sys.argv\n'
                'counter=pathlib.Path("attempt_counter")\n'
                'n=int(counter.read_text())+1 if counter.exists() else 1\n'
                'counter.write_text(str(n))\n'
                'if n==1:\n'
                '  print("429 rate limit exceeded",file=sys.stderr)\n'
                '  sys.exit(1)\n'
                'result=args[args.index("--output-last-message")+1]\n'
                'data={"approved":True,"summary":"ok","ui_fixes":"","backend_fixes":""}\n'
                'open(result,"w").write(json.dumps(data))\n'
            )
            exe.chmod(0o755)
            with patch.object(orch, 'ROOT', root), patch.object(orch, 'DATA', root / '.orchestrator'), patch.object(orch, 'STATE_FILE', root / '.orchestrator/state.json'), patch.object(orch, 'LOGS', root / '.orchestrator/logs'), patch.object(orch, 'COOLDOWN_SEC', 0), patch.dict(os.environ, {'PATH':f'{bindir}:'+os.environ['PATH']}):
                state = {'sol_cooldown_until': 0}
                result = asyncio.run(orch.sol_call(state, 'review', orch.REVIEW_SCHEMA, 'Review work'))
                self.assertTrue(result['approved'])
                self.assertEqual(state['sol_attempt'], 2)

    def test_mocked_parallel_cli_and_session_saving(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            root = tmp / 'repo'
            root.mkdir()
            bindir = tmp / 'bin'
            bindir.mkdir()
            ui = bindir / 'agy'
            ui.write_text('#!/usr/bin/env python3\nimport json\nprint(json.dumps({"event":"init","conversation_id":"ag123"}),flush=True)\nprint(json.dumps({"event":"result","result":{"status":"SUCCESS","conversation_id":"ag123","response":"UI completed"}}),flush=True)\n')
            backend = bindir / 'opencode'
            backend.write_text('#!/usr/bin/env python3\nimport json\nprint(json.dumps({"type":"step_start","sessionID":"ses_abc"}),flush=True)\nprint(json.dumps({"type":"text","sessionID":"ses_abc","part":{"text":"Backend completed"}}),flush=True)\n')
            ui.chmod(0o755)
            backend.chmod(0o755)
            state = {'plan': {'architecture':'a','api_contract':'b','ui_paths':['frontend'], 'backend_paths':['backend'], 'ui_task':'UI', 'backend_task':'API', 'suggested_verification':'none'}, 'workers': {}}
            for k in ('ui','backend'):
                state['workers'][k] = {'status':'pending','session_id':'','attempt':0, 'next_run':0, 'error':'', 'result':'','revision':''}
            with patch.object(orch, 'ROOT', root), patch.object(orch, 'DATA', root / '.orchestrator'), patch.object(orch, 'STATE_FILE', root / '.orchestrator/state.json'), patch.object(orch, 'LOGS', root / '.orchestrator/logs'), patch.dict(os.environ, {'PATH':f'{bindir}:'+os.environ['PATH']}):
                async def jobs():
                    await asyncio.gather(orch.run_worker('ui',state), orch.run_worker('backend',state))
                asyncio.run(jobs())
                self.assertEqual(state['workers']['ui']['status'],'done')
                self.assertEqual(state['workers']['backend']['status'],'done')
                self.assertEqual(state['workers']['ui']['session_id'],'ag123')
                self.assertEqual(state['workers']['backend']['session_id'],'ses_abc')
                self.assertTrue((root/'.orchestrator/state.json').exists())


if __name__ == '__main__':
    unittest.main()
