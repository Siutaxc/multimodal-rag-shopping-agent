param(
    [ValidateSet("Enable", "Disable")]
    [string]$Action = "Enable",
    [string]$ApiBaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

$workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$composeFile = Join-Path $workspaceRoot "infra\docker-compose.yml"
$degradationFile = Join-Path $workspaceRoot "infra\docker-compose.degradation.yml"
$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCommand) {
    throw "Docker CLI was not found."
}
if ($ApiBaseUrl -notmatch '^https?://') {
    throw "ApiBaseUrl must use HTTP or HTTPS."
}

$composeArgs = @(
    "compose",
    "--project-directory", $workspaceRoot,
    "-f", $composeFile
)
if ($Action -eq "Enable") {
    $composeArgs += @("-f", $degradationFile)
}

& $dockerCommand.Source @composeArgs up -d --wait api
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($Action -eq "Enable") {
    $body = @{
        query = "metro commute ANC over ear stage9 degradation"
        mode = "rerank"
        page_size = 3
        filters = @{
            category = "over_ear"
            price_max = 1000
            currency = "CNY"
            anc = $true
        }
    } | ConvertTo-Json -Depth 6 -Compress
    $response = Invoke-RestMethod -Uri "$ApiBaseUrl/api/v1/search" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 20
    if ($response.retrieval_mode -ne "hybrid_rrf_fallback" -or -not $response.trace.degraded_reason) {
        throw "Expected the reranker fault to produce an explicit RRF fallback."
    }
    [pscustomobject]@{
        mode = "degradation-enabled"
        retrieval_mode = $response.retrieval_mode
        degraded_reason = $response.trace.degraded_reason
        result_count = @($response.items).Count
        database_changed = $false
    } | ConvertTo-Json
} else {
    [pscustomobject]@{
        mode = "fixture-restored"
        api = $ApiBaseUrl
        database_changed = $false
    } | ConvertTo-Json
}
