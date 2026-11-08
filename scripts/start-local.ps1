# FR01–12 / NFR06: Windows entry point for the prepared WSL API and native Vite.
param([ValidateSet('api', 'web', 'verify', 'browser-api', 'backup')][string]$Component = 'web')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
switch ($Component) {
    'api' { & wsl.exe -d Ubuntu -- bash scripts/start-local-api.sh }
    'browser-api' { & wsl.exe -d Ubuntu -- bash scripts/start-local-api.sh --browser-tests }
    'backup' { & wsl.exe -d Ubuntu -- bash scripts/backup-local.sh --dump-only }
    'web' {
        Set-Location -LiteralPath (Join-Path $projectRoot 'frontend')
        & npm.cmd run dev
    }
    'verify' { & wsl.exe -d Ubuntu -- bash scripts/verify-local.sh }
}
exit $LASTEXITCODE
