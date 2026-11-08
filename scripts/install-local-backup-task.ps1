# NFR07: install a user-scoped daily local dump; never handle credential values.
# Run explicitly from PowerShell after reviewing the presentation backup plan.
$ErrorActionPreference = 'Stop'
$entry = Join-Path $PSScriptRoot 'start-local.ps1'
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskName = 'ThinkMedia local daily backup'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw 'The ThinkMedia backup task already exists. Inspect it before replacing it.'
}
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "' + $entry + '" backup')
$trigger = New-ScheduledTaskTrigger -Daily -At '02:00'
$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'NFR07: private local ThinkMedia PostgreSQL dump; requires existing WSL runtime. Uses local Windows time; user must be logged in.' | Select-Object TaskName,State
