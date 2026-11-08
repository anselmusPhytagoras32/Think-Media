# THINKMEDIA_UI_DENIAL_FIX_V2
#!/usr/bin/env python3
"""One-repository supervisor: Codex CLI (Sol), Antigravity (Gemini), OpenCode (DeepSeek).

Run with `python orchestrator.py start "Build ..."`, then `resume` or `status`.
Requires: Python 3.10+, and authenticated codex, agy and opencode CLIs.
No OpenAI API key or Agents SDK needed.
"""
from __future__ import annotations

import asyncio
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from collections import deque
from typing import Literal


ROOT = Path.cwd().resolve()
DATA = ROOT / ".orchestrator"
STATE_FILE = DATA / "state.json"
LOCK_FILE = DATA / "runner.lock"
LOGS = DATA / "logs"
COOLDOWN_SEC = int(os.environ.get("COOLDOWN_SECONDS", "18000"))
SOL_MODEL = os.environ.get("SOL_MODEL", "gpt-6.1-sol")
UI_MODEL = os.environ.get("UI_MODEL", "gemini-3.8-flash-medium")
BACKEND_MODEL = os.environ.get("BACKEND_MODEL", "deepseek/deepseek-flash")
MAX_REVIEW_ROUNDS = int(os.environ.get("MAX_REVIEW_ROUNDS", "2"))
QUOTA = re.compile(r"rate.?limit|quota.?exceed|resource.?exhaust|too many requests|\b429\b|usage limit|quota exhausted|reset[s]? in|try again after.*hour", re.I)
PERMANENT = re.compile(r"insufficient (balance|credits)|billing|payment required|invalid (api )?key|unauthoriz|forbidden|context (window|length)|maximum context", re.I)


PLAN_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "architecture": {"type": "string"},
        "api_contract": {"type": "string"},
        "ui_paths": {"type": "array", "items": {"type": "string"}},
        "backend_paths": {"type": "array", "items": {"type": "string"}},
        "ui_task": {"type": "string"},
        "backend_task": {"type": "string"},
        "suggested_verification": {"type": "string"},
    },
    "required": ["architecture", "api_contract", "ui_paths", "backend_paths",
                 "ui_task", "backend_task", "suggested_verification"],
}
REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "approved": {"type": "boolean"},
        "summary": {"type": "string"},
        "ui_fixes": {"type": "string"},
        "backend_fixes": {"type": "string"},
    },
    "required": ["approved", "summary", "ui_fixes", "backend_fixes"],
}



def brief_event(role: str, event: dict) -> str | None:
    """Summarize provider events without dumping enormous token streams."""
    kind = str(event.get("type") or event.get("event") or "")
    if role == "sol":
        if kind == "thread.started":
            return "Codex session started"
        if kind == "turn.started":
            return "Analyzing task"
        if kind in ("item.started", "item.completed", "item.updated"):
            item = event.get("item") or {}
            item_type = item.get("type", "item")
            if item_type == "command_execution":
                command = str(item.get("command", ""))
                return f"{kind.split('.')[-1]} command: {command[:105]}"
            if item_type == "agent_message" and kind == "item.completed":
                message = " ".join(str(item.get("text", "")).split())
                return f"Message: {message[:150]}" if message else "Produced plan/review message"
            if kind != "item.updated":
                return f"{kind.split('.')[-1]} {item_type}"
        if kind == "turn.completed":
            usage = event.get("usage") or {}
            return f"Codex turn finished; tokens={usage.get('input_tokens', '?')} in / {usage.get('output_tokens', '?')} out"
        if kind in ("turn.failed", "error"):
            return f"Codex error: {str(event.get('message') or event.get('error') or kind)[:145]}"
        return None
    if role == "ui":
        if kind in ("init", "start", "session_start"):
            return "Gemini session started"
        if kind in ("tool_call", "tool_use", "tool_result"):
            tool = event.get("tool") or event.get("name") or (event.get("data") or {}).get("name") or "tool"
            return f"{kind}: {str(tool)[:85]}"
        if kind in ("step_update", "status", "progress"):
            part = event.get("step_update") or event.get("data") or {}
            text = part.get("description") or part.get("message") or part.get("status") or "working"
            return f"Progress: {str(text)[:125]}"
        if kind == "result":
            result = event.get("result") or {}
            return f"Gemini result: {result.get('status', 'finished')}"
        return None
    if role == "backend":
        if kind in ("step_start", "session_start"):
            return "DeepSeek step started"
        if kind in ("tool_use", "tool_result", "tool"):
            part = event.get("part") or {}
            tool = part.get("tool") or part.get("name") or "tool"
            return f"{kind}: {str(tool)[:90]}"
        if kind == "error":
            return f"OpenCode error: {str(event.get('error'))[:160]}"
        if kind in ("step_finish", "step_end"):
            return "DeepSeek step finished"
        return None
    return None


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save(state: dict) -> None:
    DATA.mkdir(exist_ok=True)
    state["updated_at"] = now()
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_FILE)


def read_state() -> dict:
    if not STATE_FILE.exists():
        raise SystemExit("No existing run. Start with: python orchestrator.py start 'your task'")
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def quota_error(s: str) -> bool:
    return bool(QUOTA.search(s) and not PERMANENT.search(s))


def project_specs() -> str:
    """Read compact local SRS-derived files; do not assume DOCX can be parsed by CLIs."""
    chunks = []
    for rel in ("AGENTS.md", ".ai-team/AGENT_RULES.md", ".ai-team/spec/THINKMEDIA_AGENT_BRIEF.md", ".ai-team/spec/THINKMEDIA_PHASES.md"):
        path = ROOT / rel
        if path.is_file():
            chunks.append(f"\n### {rel}\n{path.read_text(encoding='utf-8', errors='replace')[:24000]}")
    return "\n".join(chunks)[:60000]


def inventory() -> str:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit("Run this from the root of an existing Git repository.")
    tracked = result.stdout.splitlines()
    readme = ROOT / "README.md"
    description = readme.read_text(encoding="utf-8", errors="replace")[:5000] if readme.exists() else ""
    # Include a short listing of new source files in a partially built project.
    extra = []
    for child in sorted(ROOT.rglob('*')):
        if len(extra) >= 160:
            break
        if child.is_file():
            rel = child.relative_to(ROOT).as_posix()
            if any(part in {'.git', '.orchestrator', '.ai-team', '.venv', 'node_modules', 'dist', 'build', '__pycache__'} for part in child.relative_to(ROOT).parts):
                continue
            if not any(part.startswith('.') or part.endswith(('.pem', '.key')) for part in child.relative_to(ROOT).parts):
                extra.append(rel)
    return "TRACKED FILES:\n" + "\n".join(tracked[:400]) + "\nDISCOVERED FILES:\n" + "\n".join(extra) + "\nREADME:\n" + description


def validate_paths(plan: dict) -> None:
    def norm(path: str) -> str:
        s = path.replace("\\", "/").rstrip("/")
        if not s or s in (".", "*") or s.startswith("/") or ".." in s.split("/"):
            raise ValueError(f"Unsafe/unbounded ownership path: {path!r}")
        return s
    if not plan["ui_paths"] or not plan["backend_paths"]:
        raise ValueError("Both workers must own some specific files/directories")
    ui = [norm(p) for p in plan["ui_paths"]]
    backend = [norm(p) for p in plan["backend_paths"]]
    for a in ui:
        for b in backend:
            if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                raise ValueError(f"UI/backend ownership overlaps: {a} vs {b}")


async def sol_call(state: dict, stage: str, schema: dict, prompt: str) -> dict:
    """Call the signed-in Codex CLI; retry quota errors after a durable cooldown.

    This invocation uses ChatGPT subscription login if `codex login` did.
    Neither OpenAI API keys nor Python SDKs are used.
    """
    DATA.mkdir(exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    schema_file = DATA / f"sol-{stage}-schema.json"
    output_file = DATA / f"sol-{stage}-result.json"
    schema_file.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    while True:
        wait_until = state.get("sol_cooldown_until", 0)
        if wait_until > time.time():
            delay = wait_until - time.time()
            print(f"[Sol/{stage}] quota cooldown {delay/3600:.2f}h", flush=True)
            await asyncio.sleep(delay)
        state["sol_attempt"] = state.get("sol_attempt", 0) + 1
        save(state)
        output_file.unlink(missing_ok=True)
        log_path = LOGS / f"sol-{stage}-attempt-{state['sol_attempt']}.log"
        cmd = ["codex", "exec", "--json", "--model", SOL_MODEL,
               "--sandbox", "read-only", "--output-schema", str(schema_file),
               "--output-last-message", str(output_file), "-"]
        print(f"[Sol/{stage}] invoking Codex CLI ({log_path.relative_to(ROOT)})", flush=True)
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, cwd=str(ROOT), stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            raise RuntimeError(f"Could not launch Codex CLI: {exc}") from exc
        state["sol_pid"] = process.pid
        save(state)
        # Stream outputs immediately. Earlier versions only wrote the log after
        # communicate() returned, making planning appear frozen for minutes.
        recent_lines = deque(maxlen=350)
        last_notice = {"text": "", "at": 0.0}
        async def drain(reader, source, fp):
            async for line in reader:
                decoded = line.decode("utf-8", errors="replace").rstrip("\r\n")
                fp.write(f"[{source}] {decoded}\n")
                fp.flush()
                recent_lines.append(decoded[-3000:])
                if source == "stdout":
                    try:
                        evt = json.loads(decoded)
                    except ValueError:
                        continue
                    message = brief_event("sol", evt)
                    if message and (message != last_notice["text"] or time.time() - last_notice["at"] > 20):
                        print(f"[Sol/{stage}] {message}", flush=True)
                        last_notice.update(text=message, at=time.time())
                elif re.search(r"(error|failed|429|quota|rate.limit)", decoded, re.I):
                    print(f"[Sol/{stage}][stderr] {decoded[:180]}", flush=True)
        try:
            with log_path.open("w", encoding="utf-8") as fp:
                process.stdin.write(prompt.encode("utf-8"))
                await process.stdin.drain()
                process.stdin.close()
                await asyncio.gather(drain(process.stdout, "stdout", fp), drain(process.stderr, "stderr", fp))
                await process.wait()
        finally:
            state["sol_pid"] = None
            save(state)
        diagnostic = "\n".join(recent_lines)
        if process.returncode == 0 and output_file.exists():
            try:
                parsed = json.loads(output_file.read_text(encoding="utf-8"))
            except (ValueError, OSError) as exc:
                raise RuntimeError(f"Codex returned malformed JSON; inspect {log_path}") from exc
            for key in schema["required"]:
                if key not in parsed:
                    raise RuntimeError(f"Codex result missing required key {key!r}; inspect {log_path}")
            state["sol_cooldown_until"] = 0
            save(state)
            return parsed
        if quota_error(diagnostic):
            state["sol_cooldown_until"] = time.time() + COOLDOWN_SEC
            save(state)
            print(f"[Sol/{stage}] quota detected; retry in {COOLDOWN_SEC/3600:.1f}h", flush=True)
            continue
        raise RuntimeError(
            f"Codex CLI failed in {stage}, exit={process.returncode}; inspect {log_path}"
        )


def write_plan_note(plan: dict) -> None:
    DATA.mkdir(exist_ok=True)
    (DATA / "plan.md").write_text(
        f"# Sol's plan (read-only for workers)\n\n## Architecture\n{plan['architecture']}\n\n"
        f"## Shared API contract\n{plan['api_contract']}\n\n"
        f"## UI ownership\n{', '.join(plan['ui_paths'])}\n\n"
        f"## Backend ownership\n{', '.join(plan['backend_paths'])}\n\n"
        f"## Verification suggestion\n{plan['suggested_verification']}\n",
        encoding="utf-8",
    )


async def ensure_plan(state: dict) -> None:
    if "plan" in state:
        plan_note = DATA / "plan.md"
        if not plan_note.exists():
            write_plan_note(state["plan"])
        return
    planner_prompt = (
        "You are GPT-6.1 Sol, senior software architect coordinating TWO implementation "
        "workers in ONE shared repository. Return a structured plan matching the provided schema. "
        "Delegate UI to Gemini/Antigravity with Intent and Impeccable skills, backend to "
        "DeepSeek/OpenCode. Define exact, shared API contracts BEFORE coding. "
        "Assign DISJOINT file/directory ownership (avoid broad parents, e.g. src/, "
        "when backend uses src/api/). Workers can READ all files but WRITE only within "
        "owned paths. Shared configs or dependency changes must have ONE designated file owner, never both. "
        "Keep each worker task specific and testable. No production operations. "
        "The frontend agent must actually open Intent and Impeccable SKILL.md documents. If clarification is needed, the complete source is in .ai-team/spec/ThinkMedia_Full_SRS_Extract.txt. "
        f"\n\nCANONICAL PROJECT SPECIFICATION:\n{project_specs()}"
        f"\n\nUSER GOAL:\n{state['request']}\n\nREPOSITORY:\n{inventory()}"
    )
    plan = await sol_call(state, "plan", PLAN_SCHEMA, planner_prompt)
    validate_paths(plan)
    state["plan"] = plan
    for role in ("ui", "backend"):
        state["workers"][role] = {
            "status": "pending", "session_id": "", "attempt": 0,
            "next_run": 0, "error": "", "result": "", "revision": ""
        }
    state["phase"] = "working"
    save(state)
    write_plan_note(state["plan"])
    print("[Sol] Plan saved to .orchestrator/plan.md", flush=True)


def worker_prompt(role: Literal["ui", "backend"], state: dict) -> str:
    plan = state["plan"]
    own = plan["ui_paths" if role == "ui" else "backend_paths"]
    other = plan["backend_paths" if role == "ui" else "ui_paths"]
    task = plan["ui_task" if role == "ui" else "backend_task"]
    revision = state["workers"][role].get("revision", "")
    common = (
        "You are coding inside ONE shared Git repository. Your permitted WRITE paths are: "
        f"{own}. You may READ everything, but MUST NOT WRITE these other-agent paths: {other}. "
        "Do not change shared configuration, dependencies, lockfiles, schemas or migrations outside "
        "your ownership; report what must be changed to the orchestrator instead. "
        "Do not deploy, push, handle real secrets, or modify production resources. "
        "Read AGENTS.md, .ai-team/AGENT_RULES.md, .ai-team/spec/THINKMEDIA_AGENT_BRIEF.md, .ai-team/spec/THINKMEDIA_PHASES.md "
        "and .orchestrator/plan.md first; follow the API contract and current phase only. "
        "This is a coding task: implement and test, not just describe. "
        "Conclude with changed paths, tests run, and unresolved issues."
    )
    if role == "ui":
        common += (
            " Before editing, discover, OPEN AND FOLLOW the installed Intent and Impeccable SKILL.md "
            "documents. Use Intent for user flows and Impeccable for visual design. "
            "If either skill is missing, report that clearly rather than pretending it was used."
        )
    if role == "ui":
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
    return f"{common}\n\nAssigned task:\n{task}\n\nRevision requested:\n{revision or '(initial implementation)'}"


async def run_worker(role: Literal["ui", "backend"], state: dict) -> None:
    worker = state["workers"][role]
    while worker["status"] not in ("done", "failed"):
        delay = worker.get("next_run", 0) - time.time()
        if delay > 0:
            print(f"[{role}] cooling down for {delay/3600:.2f}h", flush=True)
            await asyncio.sleep(delay)
        worker["status"] = "running"
        worker["attempt"] += 1
        worker["next_run"] = 0
        save(state)

        prompt = worker_prompt(role, state)
        if worker["session_id"]:
            prompt = "Continue the unfinished assigned task from our earlier session.\n" + prompt
        if role == "ui":
            cmd = ["agy", "-p", prompt, "--model", UI_MODEL, "--mode=accept-edits", "--output-format", "stream-json"]
            if worker["session_id"]:
                cmd.extend(["--conversation", worker["session_id"]])
        else:
            cmd = ["opencode", "run", "--model", BACKEND_MODEL, "--agent", "build", "--format", "json"]
            # Only use unattended approval on an intentionally trusted machine.
            if os.environ.get("OPENCODE_AUTO", "1") == "1":
                cmd.append("--auto")
            if worker["session_id"]:
                cmd.extend(["--session", worker["session_id"]])
            cmd.append(prompt)

        LOGS.mkdir(parents=True, exist_ok=True)
        log_path = LOGS / f"{role}-attempt-{worker['attempt']}.log"
        print(f"[{role}] starting attempt {worker['attempt']} ({log_path.relative_to(ROOT)})", flush=True)
        last_error = []
        terminal = {}
        last_ui_commands = []   # last requested commands; denial may occur on an earlier command
        ui_permission_errors = []
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, cwd=str(ROOT), stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            worker["status"] = "failed"
            worker["error"] = f"Unable to start CLI: {exc}"
            save(state)
            return

        worker["pid"] = process.pid
        save(state)
        async def consume(reader, label, fp):
            last_notice = ""
            last_notice_at = 0.0
            async for line in reader:
                s = line.decode("utf-8", errors="replace").rstrip("\n")
                fp.write(f"[{label}] {s}\n")
                fp.flush()
                if label == "stderr":
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
                    continue
                try:
                    evt = json.loads(s)
                except ValueError:
                    continue
                notice = brief_event(role, evt)
                if notice and (notice != last_notice or time.time() - last_notice_at > 20):
                    print(f"[{role}] {notice}", flush=True)
                    last_notice, last_notice_at = notice, time.time()
                if role == "ui":
                    step = evt.get("step_update") or {}
                    if (step.get("step_type") == "tool" and step.get("tool_name") == "run_command"
                            and step.get("state") == "ACTIVE"):
                        params = (step.get("tool_info") or {}).get("parameters") or {}
                        command = str(params.get("CommandLine") or params.get("command") or "").strip()
                        if command:
                            last_ui_commands.append(command)
                            del last_ui_commands[:-10]
                            print(f"[ui] requested shell command: {command[:180]}", flush=True)
                sess = evt.get("conversation_id") if role == "ui" else evt.get("sessionID")
                if not sess and role == "ui":
                    sess = evt.get("result", {}).get("conversation_id") or evt.get("step_update", {}).get("conversation_id")
                if not sess and role == "backend":
                    sess = evt.get("part", {}).get("sessionID")
                if sess and sess != worker["session_id"]:
                    worker["session_id"] = sess
                    save(state)
                if (role == "ui" and evt.get("event") == "result"):
                    terminal.update(evt.get("result", {}))
                if (role == "backend" and evt.get("type") == "error"):
                    terminal["error"] = evt.get("error") or evt.get("part") or "unknown error"
                if (role == "backend" and evt.get("type") == "text"):
                    text_part = evt.get("part", {}).get("text", "")
                    terminal["last_text"] = (terminal.get("last_text", "") + text_part)[-3000:]

        with log_path.open("w", encoding="utf-8") as fp:
            await asyncio.gather(
                consume(process.stdout, "stdout", fp),
                consume(process.stderr, "stderr", fp),
            )
            exit_code = await process.wait()
        worker["pid"] = None
        save(state)

        details = json.dumps(terminal, ensure_ascii=False) + "\n" + "\n".join(last_error)
        worker["result"] = str(terminal.get("response") or terminal.get("last_text") or "")[-2500:]
        worker["error"] = details[-2500:] if exit_code != 0 or terminal.get("error") or re.search(r"soft.denied|auto.denied|headless mode cannot prompt|jetski: no output produced", details, re.I) else ""
        worker["log"] = str(log_path.relative_to(ROOT))
        ui_denied = bool(role == "ui" and (ui_permission_errors or terminal.get("denied_actions")))
        if ui_denied:
            suspect = last_ui_commands[-1] if last_ui_commands else "unknown"
            worker["blocked_command_candidate"] = suspect
            worker["error"] = (f"UI_PERMISSION_DENIED; last requested command (candidate): {suspect}\n" + details)[-2500:]
            # Retry should start a fresh conversation, not inherit the denied one.
            worker["session_id"] = ""
        else:
            worker["blocked_command_candidate"] = ""
        successful = (
            not ui_denied and
            exit_code == 0
            and not terminal.get("error")
            and (role != "ui" or terminal.get("status") == "SUCCESS")
            and not re.search(r"permission.*(denied|approval|required)|soft.denied|soft.denial|auto.denied|tool.*denied|headless mode cannot prompt|jetski: no output produced", details, re.I)
        )
        if successful:
            worker["status"] = "done"
            worker["revision"] = ""
            print(f"[{role}] complete", flush=True)
        elif quota_error(details):
            worker["status"] = "cooldown"
            worker["next_run"] = time.time() + COOLDOWN_SEC
            print(f"[{role}] quota reached; will resume after {COOLDOWN_SEC/3600:.1f}h", flush=True)
        else:
            worker["status"] = "failed"
            print(f"[{role}] failed; check {worker['log']}", flush=True)
        save(state)


def run_verification() -> str:
    setting = os.environ.get("VERIFY_COMMAND", "").strip()
    if not setting:
        return "No test command configured. Verification has NOT been run."
    argv = shlex.split(setting)
    if not argv:
        return "No test command configured."
    try:
        proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=600)
        return f"Command: {setting}\nExit: {proc.returncode}\n{(proc.stdout + proc.stderr)[-6000:]}"
    except Exception as exc:
        return f"Verification command failed to launch: {exc}"


async def review(state: dict) -> bool:
    diff = subprocess.run(["git", "diff", "--", "."], cwd=ROOT, capture_output=True, text=True)
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True)
    untracked_excerpts = []
    for rel in untracked.stdout.splitlines()[:15]:
        if rel.startswith((".orchestrator/", ".git/", "node_modules/")) or re.search(
            r"(^|/)(\.env|secret|credential|.*\.key)(/|$)", rel, re.I
        ):
            continue
        p = (ROOT / rel).resolve()
        try:
            if p.is_relative_to(ROOT) and p.is_file() and p.stat().st_size < 20000:
                untracked_excerpts.append(f"### {rel}\n{p.read_text(encoding='utf-8', errors='replace')[:1200]}")
        except OSError:
            continue
    tests = run_verification()
    state["verification"] = tests
    save(state)
    reviewer_prompt = (
        "You are GPT-6.1 Sol, integration reviewer. Assess the two implementation "
        "worker summaries, Git diff excerpts, untracked file snippets, and test output. "
        "Do not claim tests passed without evidence. Only set approved=true when verified AND the intended feature visibly exists. "
        "Request precise ui_fixes and backend_fixes when needed (empty strings otherwise). "
        "Do not ask for production deployment. Return a JSON object matching the schema.\n\n"
        f"Canonical specification: {project_specs()[:30000]}\n"
        f"Project goal: {state['request']}\nPlan: {json.dumps(state['plan'])}\n"
        f"Worker results: {json.dumps(state['workers'])[-6500:]}\n"
        f"Git diff excerpt:\n{diff.stdout[:19000]}\n"
        f"Untracked files:\n{untracked.stdout[:2500]}\n"
        f"Untracked content excerpts:\n{chr(10).join(untracked_excerpts)[:6500]}\nVerification:\n{tests}"
    )
    result = await sol_call(state, "review", REVIEW_SCHEMA, reviewer_prompt)
    # Never advance phases on a model claim without an actual successful verification run.
    verified = bool(os.environ.get("VERIFY_COMMAND", "").strip()) and "Exit: 0\n" in tests
    if result["approved"] and not verified:
        result["approved"] = False
        result["summary"] += " Verification missing or failed: cannot approve."
        if not (result["ui_fixes"] or result["backend_fixes"]):
            state["phase"] = "needs_attention"
    state["review"] = result
    save(state)
    print(f"[Sol] {result['summary']}", flush=True)
    if result["approved"]:
        return True
    if state["review_round"] >= MAX_REVIEW_ROUNDS or not (result["ui_fixes"] or result["backend_fixes"]):
        state["phase"] = "needs_attention"
        save(state)
        return True
    state["review_round"] += 1
    for role, fixes in (("ui", result["ui_fixes"]), ("backend", result["backend_fixes"])):
        if fixes.strip():
            worker = state["workers"][role]
            worker["status"] = "pending"
            worker["next_run"] = 0
            worker["revision"] = fixes
    state["phase"] = "working"
    save(state)
    return False


async def run_all(state: dict) -> None:
    await ensure_plan(state)
    while True:
        if state["phase"] == "working":
            await asyncio.gather(*(run_worker(role, state) for role in ("ui", "backend")))
            failed = [role for role, task in state["workers"].items() if task["status"] == "failed"]
            if failed:
                state["phase"] = "needs_attention"
                save(state)
                print(f"Failed workers: {', '.join(failed)}. Fix and use 'retry <role>'.")
                return
            state["phase"] = "review"
            save(state)
        if state["phase"] == "review":
            completed = await review(state)
            if not completed:
                continue
            if state["phase"] == "review":
                state["phase"] = "complete"
                save(state)
            return
        return


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python orchestrator.py start 'goal' | status | resume | retry ui|backend")
    action = sys.argv[1]
    if action == "status":
        state = read_state()
        print(json.dumps({"phase": state["phase"], "workers": state["workers"], "review": state.get("review")}, indent=2))
        return
    DATA.mkdir(exist_ok=True)
    with LOCK_FILE.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Another orchestrator is already running.")
        if action == "start":
            if len(sys.argv) < 3:
                raise SystemExit("Specify a project goal in quotes.")
            if STATE_FILE.exists() and read_state().get("phase") != "complete":
                raise SystemExit("An unfinished run exists. Use 'resume' or 'status'.")
            state = {"request": " ".join(sys.argv[2:]), "phase": "planning", "workers": {},
                     "sol_cooldown_until": 0, "sol_attempt": 0, "review_round": 0, "created_at": now()}
            save(state)
        elif action in ("resume", "retry"):
            state = read_state()
            if action == "retry":
                if len(sys.argv) != 3 or sys.argv[2] not in ("ui", "backend"):
                    raise SystemExit("Usage: python orchestrator.py retry ui|backend")
                role = sys.argv[2]
                state["workers"][role]["status"] = "pending"
                state["workers"][role]["next_run"] = 0
                state["phase"] = "working"
                save(state)
            elif state["phase"] == "needs_attention":
                raise SystemExit("A task needs attention. Check status/logs, then use 'retry ui' or 'retry backend'.")
        else:
            raise SystemExit("Unknown command")
        for worker in state.get("workers", {}).values():
            if worker["status"] == "running":
                worker["status"] = "pending"  # interrupted process; continue saved CLI session
        save(state)
        try:
            asyncio.run(run_all(state))
        except KeyboardInterrupt:
            print("Stopped. Run `python orchestrator.py resume` to continue.")
        except Exception as exc:
            print(f"Orchestrator stopped: {exc}\nInspect state/logs; run 'resume' when resolved.", file=sys.stderr)
            raise
        print(f"Final phase: {state['phase']}")


if __name__ == "__main__":
    main()
