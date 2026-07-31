$ErrorActionPreference = "Stop"

$workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$composeFile = Join-Path $workspaceRoot "infra\docker-compose.yml"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI was not found."
}

& docker compose --project-directory $workspaceRoot -f $composeFile down
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
