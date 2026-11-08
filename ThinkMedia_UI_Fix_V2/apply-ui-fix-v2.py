#!/usr/bin/env python3
"""ThinkMedia Antigravity UI worker diagnostic patch, format-tolerant revision.

This patch handles the original and live-monitor supervisor variants without
matching the whole final worker-status section.  It backs up before mutations,
keeps other workers/state unchanged, and never installs tools or grants all
terminal commands.
"""
import argparse
import ast
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys

TAG = "# THINKMEDIA_UI_DENIAL_FIX_V2"
ROOT = Path.cwd()
SCRIPT = ROOT / ".ai-team" / "orchestrator.py"
SETTINGS = Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
STATE = ROOT / ".orchestrator" / "state.json"
EXTRA_RULES = (
    "command(wc)",
    "command(head)",
    "command(tail)",
    "command(.agent/skills/impeccable/scripts/impeccable context)",
    "command(.agent/skills/impeccable/scripts/impeccable detect)",
)


def once(source, old, new, label):
    if source.count(old) != 1:
        raise RuntimeError(f"Unexpected orchestrator layout near {label}: found {source.count(old)} anchors; no changes made")
    return source.replace(old, new, 1)


def function(source: str, name: str) -> tuple[int,int,str]:
    tree = ast.parse(source)
    matches = [x for x in tree.body if isinstance(x, (ast.FunctionDef,ast.AsyncFunctionDef)) and x.name == name]
    if len(matches) != 1:
        raise RuntimeError(f"Could not uniquely locate {name}() in orchestrator; no changes made")
    start = sum(len(line) for line in source.splitlines(keepends=True)[:matches[0].lineno-1])
    end = sum(len(line) for line in source.splitlines(keepends=True)[:matches[0].end_lineno])
    return start,end,source[start:end]


def build_patch(source):
    if TAG in source:
        return source, False
    start,end,section = function(source,"worker_prompt")
    section = once(section,
        '    return f"{common}\\n\\nAssigned task:',
        '''    if role == "ui":
        common += (
            " IMPORTANT: In headless mode, prefer native list_dir, view_file, read_file, "
            "grep_search, write_to_file and replace_file_content tools for file operations. "
            "Avoid run_command for listing or reading files (ls, cat, wc, git status, etc.). "
            "Only use shell commands when a build/test or the Impeccable executable genuinely "
            "requires them. Avoid shell redirections/pipelines unless permitted. If a command "
            "is blocked, stop and report the requested command; never claim coding completed. "
            "For new UI use Impeccable's init workflow and derive any permitted product context "
            "from the SRS, marking any assumptions; do not write outside assigned paths."
        )
    return f"{common}\\n\\nAssigned task:''',
        "frontend file-tool guidance")
    source = source[:start]+section+source[end:]
    start,end,section = function(source,"run_worker")
    section = once(section, '        terminal = {}\n',
        '''        terminal = {}
        last_ui_commands = []   # last requested commands; denial may occur on an earlier command
        ui_permission_errors = []
''', "worker diagnostics initialization")
    section = once(section,
        '''                if label == "stderr":
                    last_error.append(s[-1500:])
                    del last_error[:-25]
                    continue''',
        '''                if label == "stderr":
                    last_error.append(s[-1500:])
                    del last_error[:-25]
                    if role == "ui" and any(x in s.lower() for x in (
                        "headless mode cannot prompt", "auto-denied", "jetski: no output produced"
                    )):
                        ui_permission_errors.append(s)
                        suspect = last_ui_commands[-1] if last_ui_commands else "unknown"
                        print(f"[ui] SHELL PERMISSION DENIED; last requested command (candidate): {suspect[:220]}", flush=True)
                        if process.returncode is None:
                            try:
                                process.terminate()
                            except ProcessLookupError:
                                pass
                    continue''',
        "early denial handling")
    section = once(section,
        '                sess = evt.get("conversation_id") if role == "ui" else evt.get("sessionID")',
        '''                if role == "ui":
                    step = evt.get("step_update") or {}
                    if (step.get("step_type") == "tool" and step.get("tool_name") == "run_command"
                            and step.get("state") == "ACTIVE"):
                        params = (step.get("tool_info") or {}).get("parameters") or {}
                        command = str(params.get("CommandLine") or params.get("command") or "").strip()
                        if command:
                            last_ui_commands.append(command)
                            del last_ui_commands[:-10]
                            print(f"[ui] requested shell command: {command[:180]}", flush=True)
                sess = evt.get("conversation_id") if role == "ui" else evt.get("sessionID")''',
        "UI command event logging")
    section = once(section,
        '        worker["log"] = str(log_path.relative_to(ROOT))\n',
        '''        worker["log"] = str(log_path.relative_to(ROOT))
        ui_denied = bool(role == "ui" and (ui_permission_errors or terminal.get("denied_actions")))
        if ui_denied:
            suspect = last_ui_commands[-1] if last_ui_commands else "unknown"
            worker["blocked_command_candidate"] = suspect
            worker["error"] = (f"UI_PERMISSION_DENIED; last requested command (candidate): {suspect}\\n" + details)[-2500:]
            # Retry should start a fresh conversation, not inherit the denied one.
            worker["session_id"] = ""
        else:
            worker["blocked_command_candidate"] = ""
''', "durable diagnostic state")
    section = once(section,
        '        successful = (\n',
        '        successful = (\n            not ui_denied and\n',
        "final success classifier")
    source = source[:start]+section+source[end:]
    source = TAG+'\n'+source
    ast.parse(source)
    return source,True


def fresh_backup(path, purpose):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out = path.with_name(f"{path.name}.{purpose}-{stamp}.bak")
    shutil.copy2(path,out)
    return out


def reset_failed_ui():
    if not STATE.is_file():
        print("No saved state found; nothing to reset")
        return
    state=json.loads(STATE.read_text(encoding="utf-8"))
    worker=(state.get("workers") or {}).get("ui") or {}
    if worker.get("status") != "failed":
        print("UI isn't failed; no state change")
        return
    pid=worker.get("pid")
    if pid:
        try:
            os.kill(int(pid),0)
        except (ValueError,TypeError,ProcessLookupError):
            pass
        except PermissionError:
            raise RuntimeError("UI worker PID permission unknown; stop existing process first")
        else:
            raise RuntimeError("UI worker still running; stop before resetting state")
    bak=fresh_backup(STATE,"before-ui-reset")
    worker["session_id"]=""
    STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Reset failed UI session; kept backend and Sol state. Backup: {bak.name}")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--reset-failed-ui",action="store_true")
    parser.add_argument("--check",action="store_true",help="Validate patch compatibility without writing")
    args=parser.parse_args()
    if not SCRIPT.is_file():
        raise RuntimeError(".ai-team/orchestrator.py missing. Run from the OJT_HUB project root")
    original=SCRIPT.read_text(encoding="utf-8")
    updated,changed=build_patch(original)
    print("Supervisor compatibility: OK" if changed else "Supervisor already patched")
    if args.check:
        print("Dry run only; no files changed")
        return
    # Validate settings BEFORE altering the supervisor.
    settings=None
    if SETTINGS.exists():
        settings=json.loads(SETTINGS.read_text(encoding="utf-8"))
        if not isinstance(settings,dict) or not isinstance(settings.get("permissions",{}),dict):
            raise RuntimeError("Unsupported Antigravity settings JSON; no changes made")
        if not isinstance(settings.get("permissions",{}).get("allow",[]),list):
            raise RuntimeError("Antigravity permissions.allow is not a list; no changes made")
    if changed:
        bak=fresh_backup(SCRIPT,"before-ui-fix-v2")
        SCRIPT.write_text(updated,encoding="utf-8")
        print(f"Patched supervisor. Backup: {bak.name}")
    if settings is not None:
        permissions=settings.setdefault("permissions",{})
        allowed=permissions.setdefault("allow",[])
        added=[rule for rule in EXTRA_RULES if rule not in allowed]
        if added:
            bak=fresh_backup(SETTINGS,"before-ui-fix-v2")
            allowed.extend(added)
            SETTINGS.write_text(json.dumps(settings,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            print(f"Added {len(added)} narrow command rules. Settings backup: {bak.name}")
        if permissions.get("ask") or permissions.get("deny"):
            print("WARNING: existing ask/deny rules remain; they might still block commands")
    else:
        print("WARNING: Antigravity settings file not found; no global rules changed")
    if args.reset_failed_ui:
        reset_failed_ui()
    print("No agents launched. Use ./team retry ui once after reviewing the changes.")

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, SyntaxError, RuntimeError) as exc:
        raise SystemExit(f"Patch not applied: {exc}")
