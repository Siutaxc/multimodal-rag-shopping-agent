param(
    [string]$ProjectName = ""
)

$ErrorActionPreference = "Stop"

$workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$composeFile = Join-Path $workspaceRoot "infra\docker-compose.yml"

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCommand) {
    throw "Docker CLI was not found. Install or start Docker Desktop, then rerun npm run stack:up."
}

$composeArgs = @("compose")
if ($ProjectName) {
    $composeArgs += @("--project-name", $ProjectName)
}
$composeArgs += @(
    "--project-directory", $workspaceRoot,
    "-f", $composeFile,
    "up", "-d", "--build", "--wait"
)

& $dockerCommand.Source @composeArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
