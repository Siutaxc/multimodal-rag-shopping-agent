param(
    [string]$ProjectName = "",
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$WebBaseUrl = "http://127.0.0.1:3000",
    [string]$ReportPath = "evals/reports/stage9-fixture-smoke.json"
)

$ErrorActionPreference = "Stop"

$workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$composeFile = Join-Path $workspaceRoot "infra\docker-compose.yml"
$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCommand) {
    throw "Docker CLI was not found. Install or start Docker Desktop, then rerun npm run stack:fixture."
}

$composeArgs = @("compose")
if ($ProjectName) {
    $composeArgs += @("--project-name", $ProjectName)
}
$composeArgs += @("--project-directory", $workspaceRoot, "-f", $composeFile)

& $dockerCommand.Source @composeArgs up -d --build --wait
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$containerCommands = @(
    @("python", "-m", "app.ingestion.cli", "--fixture", "data/fixtures/headphones.json"),
    @("python", "-m", "app.retrieval.index_cli"),
    @("python", "-m", "app.images.index_cli")
)

foreach ($containerCommand in $containerCommands) {
    & $dockerCommand.Source @composeArgs exec -T api @containerCommand
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

& (Join-Path $PSScriptRoot "verify-fixture.ps1") `
    -ApiBaseUrl $ApiBaseUrl `
    -WebBaseUrl $WebBaseUrl `
    -OutputPath $ReportPath
