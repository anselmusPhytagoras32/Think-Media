# Exercise the same readiness functions used by present.ps1; no app or DB writes.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'readiness.ps1')
$checkRoot = Join-Path (Split-Path $PSScriptRoot -Parent) '.local/readiness-check'
New-Item -ItemType Directory -Path $checkRoot -Force | Out-Null
$current = Get-Process -Id $PID
$script:attempts = 0
Wait-ForService 'Delayed fixture' { $script:attempts++; $script:attempts -ge 4 } $current 'fixture.log' -TimeoutSeconds 2 -PollMilliseconds 10
if ($script:attempts -ne 4) { throw 'Delayed readiness was not retried.' }
$timedOut = $false
try { Wait-ForService 'Unavailable fixture' { $false } $current 'fixture.log' -TimeoutSeconds 1 -PollMilliseconds 10 }
catch { $timedOut = $_.Exception.Message.Contains('next launch will reuse') }
if (-not $timedOut) { throw 'Unavailable service did not produce bounded, actionable timeout.' }
$state = Join-Path $checkRoot 'fixture-process.json'
Save-StartupProcess $state $checkRoot $current 'fixture.log'
$tracked = Get-StartupProcess $state $checkRoot $current.ProcessName
if ($null -eq $tracked -or $tracked.Id -ne $PID) { throw 'Live tracked process was not reused.' }
if ($tracked.StartupLog -ne 'fixture.log') { throw 'Original startup log was not preserved.' }
if ($null -ne (Get-StartupProcess $state 'different-root' $current.ProcessName)) { throw 'Foreign project process was reused.' }
$record = Get-Content -LiteralPath $state -Raw | ConvertFrom-Json
$record.startTicks = '0'
$record | ConvertTo-Json | Set-Content -LiteralPath $state -Encoding UTF8
if ($null -ne (Get-StartupProcess $state $checkRoot $current.ProcessName)) { throw 'Reused PID with a different start time was accepted.' }
$projectRoot = Split-Path $PSScriptRoot -Parent
$guard = New-Object System.Threading.Mutex($false, (Get-PresentationLockName $projectRoot))
if (-not $guard.WaitOne(0)) { throw 'A real presentation launch is still active; rerun the check when ready.' }
try {
    $duplicate = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'present.ps1')
    if ($LASTEXITCODE -ne 0 -or -not ($duplicate -join ' ').Contains('already being checked')) { throw 'A duplicate presentation launch was not prevented.' }
} finally { $guard.ReleaseMutex(); $guard.Dispose() }
Write-Output 'Readiness checks passed: delayed ready, bounded timeout, live reuse, project identity, PID reuse protection and duplicate-launch prevention.'
