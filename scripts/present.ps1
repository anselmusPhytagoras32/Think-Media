# FR01-12/NFR05-07: one-command local presentation startup on this workstation.
param([switch]$OpenBrowser,
      [ValidateRange(1,900)][int]$StartupTimeoutSeconds = 300)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'readiness.ps1')
$projectRoot = Split-Path $PSScriptRoot -Parent
$runtimeDirectory = Join-Path $projectRoot '.local'
New-Item -ItemType Directory -Path $runtimeDirectory -Force | Out-Null

function Test-ApiReady {
    try {
        $schema = Invoke-RestMethod 'http://127.0.0.1:8000/openapi.json' -TimeoutSec 2
        return $schema.info.title -eq 'ThinkMedia API'
    } catch { return $false }
}
function Test-WebReady {
    try {
        $page = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5173' -TimeoutSec 2
        return $page.StatusCode -eq 200 -and $page.Content.Contains('ThinkMedia')
    } catch { return $false }
}
$lockName = Get-PresentationLockName $projectRoot
$launchLock = New-Object System.Threading.Mutex($false, $lockName)
try { $ownsLock = $launchLock.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $ownsLock = $true }
if (-not $ownsLock) {
    Write-Output 'ThinkMedia startup is already being checked by another launch. Let that launch finish.'
    $launchLock.Dispose()
    return
}
try {
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
if (-not (Test-ApiReady)) {
    $apiErrorLog = Join-Path $runtimeDirectory "presentation-api-$stamp.err.log"
    $apiState = Join-Path $runtimeDirectory 'presentation-api-process.json'
    $api = Get-StartupProcess $apiState $projectRoot 'wsl'
    if ($null -eq $api) {
        Write-Output 'Starting ThinkMedia API. A cold WSL/library start can take several minutes.'
        $api = Start-Process -FilePath 'wsl.exe' -ArgumentList @('-d','Ubuntu','--','bash','scripts/start-local-api.sh') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDirectory "presentation-api-$stamp.log") -RedirectStandardError $apiErrorLog
        Save-StartupProcess $apiState $projectRoot $api $apiErrorLog
    } else {
        Write-Output 'Reusing the ThinkMedia API startup already in progress.'
        if ($api.StartupLog) { $apiErrorLog = $api.StartupLog }
    }
    Wait-ForService 'ThinkMedia API' { Test-ApiReady } $api $apiErrorLog -TimeoutSeconds $StartupTimeoutSeconds
}
if (-not (Test-WebReady)) {
    $webErrorLog = Join-Path $runtimeDirectory "presentation-web-$stamp.err.log"
    $webState = Join-Path $runtimeDirectory 'presentation-web-process.json'
    $web = Get-StartupProcess $webState $projectRoot 'cmd'
    if ($null -eq $web) {
        $web = Start-Process -FilePath $env:ComSpec -ArgumentList '/d /c npm.cmd run dev' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeDirectory "presentation-web-$stamp.log") -RedirectStandardError $webErrorLog
        Save-StartupProcess $webState $projectRoot $web $webErrorLog
    } elseif ($web.StartupLog) {
        $webErrorLog = $web.StartupLog
    }
    Wait-ForService 'ThinkMedia web app' { Test-WebReady } $web $webErrorLog -TimeoutSeconds $StartupTimeoutSeconds
}
Write-Output 'ThinkMedia is ready at http://127.0.0.1:5173'
if ($OpenBrowser) { Start-Process 'http://127.0.0.1:5173' }
} finally {
    $launchLock.ReleaseMutex()
    $launchLock.Dispose()
}
