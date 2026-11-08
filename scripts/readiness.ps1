# NFR05/06: readiness checks must tolerate a live, slow cold start.
function Get-PresentationLockName {
    param([string]$Root)
    return 'Local\ThinkMedia-' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Root.ToUpperInvariant())).Replace('/','_').Replace('+','-')
}

function Wait-ForService {
    param([string]$Name, [scriptblock]$Check, $Process, [string]$LogPath,
          [ValidateRange(1,900)][int]$TimeoutSeconds = 300,
          [ValidateRange(10,5000)][int]$PollMilliseconds = 500)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $nextProgress = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline) {
        if (& $Check) { return }
        $Process.Refresh()
        if ($Process.HasExited) { throw "$Name stopped during startup. See $LogPath" }
        if ((Get-Date) -ge $nextProgress) {
            Write-Output "Waiting for $Name. Its startup process is still running; logs: $LogPath"
            $nextProgress = (Get-Date).AddSeconds(15)
        }
        Start-Sleep -Milliseconds $PollMilliseconds
    }
    throw "$Name is still starting after $TimeoutSeconds seconds. The next launch will reuse this process. See $LogPath"
}

function Save-StartupProcess {
    param([string]$StatePath, [string]$Root, $Process, [string]$LogPath = '')
    $Process.Refresh()
    @{ root = $Root; pid = $Process.Id; name = $Process.ProcessName;
       startTicks = $Process.StartTime.ToUniversalTime().Ticks.ToString(); logPath = $LogPath } |
        ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding UTF8
}

function Get-StartupProcess {
    param([string]$StatePath, [string]$Root, [string]$ExpectedName)
    if (-not (Test-Path -LiteralPath $StatePath)) { return $null }
    try {
        $saved = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
        if ($saved.root -ne $Root -or $saved.name -ne $ExpectedName) { return $null }
        $candidate = Get-Process -Id $saved.pid -ErrorAction Stop
        if ($candidate.ProcessName -ne $ExpectedName -or
            $candidate.StartTime.ToUniversalTime().Ticks.ToString() -ne $saved.startTicks -or
            $candidate.HasExited) { return $null }
        $candidate | Add-Member -NotePropertyName StartupLog -NotePropertyValue $saved.logPath -Force
        return $candidate
    } catch { return $null }
}
