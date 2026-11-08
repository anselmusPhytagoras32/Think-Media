THINKMEDIA UI DENIAL REPAIR V2
=============================

The previous apply-ui-fix.py failed safely because it used an exact string
replacement that no longer matched your edited .ai-team/orchestrator.py.

This V2 uses Python function boundaries and smaller unique anchors. It was
locally tested against the original and live-monitor versions, including
an Antigravity repair-modified version, and seven existing mock tests.

Copy ThinkMedia_UI_Fix_V2.zip into your OJT_HUB project root.

1. Unzip:
   unzip -o ThinkMedia_UI_Fix_V2.zip

2. Check compatibility without changing any files:
   python3 ThinkMedia_UI_Fix_V2/apply-ui-fix-v2.py --check

3. When your agents have stopped, apply and reset the failed UI session:
   python3 ThinkMedia_UI_Fix_V2/apply-ui-fix-v2.py --reset-failed-ui

4. Retry only the UI worker:
   ./team retry ui

Monitor separately:
   ./team watch

The patch backs up the supervisor and settings.json; a reset additionally
backs up .orchestrator/state.json. It does not erase Sol's plan, backend state,
frontend files, or any credentials. It does NOT allow unrestricted commands.
If new commands are denied it prints the *last requested* command as a
candidate; this is not always the exact denied command.

The patch is format-tolerant, not universal: if --check fails, it will refuse
to modify the orchestrator. In that case, please supply the exact local
.ai-team/orchestrator.py file for a precise adaptation instead of trying
more patches or repeating model runs.

This was verified using mock CLIs only, not authenticated Antigravity access.
