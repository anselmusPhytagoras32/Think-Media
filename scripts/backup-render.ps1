# NFR07: private backup of this workstation's dedicated hosted demo.
$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
$state = Join-Path $repository '.local'
$python = Join-Path $repository 'backend/.venv/Scripts/python.exe'
$log = Join-Path $state 'hosted-backup.log'
$backupArguments = @(
    '-m', 'ops.hosted_backup',
    '--credentials-file', (Join-Path $state 'render-runtime.private.json'),
    '--pg-bin', (Join-Path $state 'pgsql/bin'),
    '--output-dir', (Join-Path $state 'hosted-backups')
)
Push-Location (Join-Path $repository 'backend')
try {
    $output = & $python @backupArguments 2>&1
    $exitCode = $LASTEXITCODE
    [IO.File]::AppendAllText($log, (($output -join [Environment]::NewLine) + [Environment]::NewLine), [Text.UTF8Encoding]::new($false))
    if ($exitCode -ne 0) { throw 'The hosted database backup failed. See the private backup log.' }
} finally {
    Pop-Location
}
