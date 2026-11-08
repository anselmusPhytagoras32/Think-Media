# Presentation startup readiness — NFR05/06

Observed failure: the launcher reported that the API was unavailable after 90
seconds, while its startup process was alive and eventually served HTTP 200.
No API crash or credential failure was observed. This was separate from the
warm non-AI request benchmark.

The hypotheses were cold library initialization, database recovery, and
contention from simultaneous local checks. An instrumented fresh import took
119.962 seconds; recommendation-module imports accounted for 92.090 cumulative
seconds, including scikit-learn initialization. These cumulative measurements
overlap and must not be added. The database setup probe included driver loading
and is not a database round-trip latency measurement. Profiling and browser
checks ran concurrently; this is diagnostic evidence, not a controlled cold
startup performance claim. Machine/cache conditions affect startup time.

The launcher now has a bounded five-minute default readiness window, configurable
with `-StartupTimeoutSeconds` (1–900), checks actual API identity, and reports
progress every 15 seconds while the process is alive. It does not equate a live
process with readiness: the API must return the expected OpenAPI title. Early
process exits still fail immediately. A saved process identity includes project,
PID and start time; retries can reuse a genuine startup without trusting a
recycled PID. A project-specific mutex prevents simultaneous launches. Log paths
are preserved across retries. No model or application decision behavior changed.

Verification:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-readiness.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/present.ps1
```

The helper checks delayed readiness, bounded failure, matching process reuse,
foreign-project rejection, PID reuse rejection and real duplicate-launch
prevention. The actual API restart subsequently completed with progress messages
and the application served HTTP 200. A ready-instance launch also returned
success. These checks cover launcher behavior; they do not prove all future
machines initialize within the configured window.
