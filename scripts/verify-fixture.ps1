param(
    [string]$ApiBaseUrl = "http://127.0.0.1:8000",
    [string]$WebBaseUrl = "http://127.0.0.1:3000",
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

function Assert-Stage9 {
    param(
        [bool]$Condition,
        [string]$Message
    )
    if (-not $Condition) {
        throw "Stage 9 fixture verification failed: $Message"
    }
}

function Invoke-JsonRequest {
    param(
        [string]$Uri,
        [string]$Method = "Get",
        [object]$Body = $null
    )
    $parameters = @{
        Uri = $Uri
        Method = $Method
        UseBasicParsing = $true
        TimeoutSec = 20
        Headers = @{ Accept = "application/json" }
    }
    if ($null -ne $Body) {
        $parameters.ContentType = "application/json"
        $parameters.Body = $Body | ConvertTo-Json -Depth 8 -Compress
    }
    $response = Invoke-WebRequest @parameters
    return [pscustomobject]@{
        StatusCode = $response.StatusCode
        Headers = $response.Headers
        Data = $response.Content | ConvertFrom-Json
    }
}

Assert-Stage9 ($ApiBaseUrl -match '^https?://') "ApiBaseUrl must use HTTP or HTTPS."
Assert-Stage9 ($WebBaseUrl -match '^https?://') "WebBaseUrl must use HTTP or HTTPS."

$ready = Invoke-JsonRequest -Uri "$ApiBaseUrl/api/v1/health/ready"
Assert-Stage9 ($ready.StatusCode -eq 200 -and $ready.Data.status -eq "ready") "API is not ready."

$products = Invoke-JsonRequest -Uri "$ApiBaseUrl/api/v1/products?page=1&page_size=100"
$fixtureProducts = @($products.Data.items | Where-Object { $_.source_name -eq "shoplens_deterministic_fixture" })
Assert-Stage9 ($products.StatusCode -eq 200) "Product endpoint did not return HTTP 200."
Assert-Stage9 ($fixtureProducts.Count -eq 24) "Expected 24 deterministic fixture products, found $($fixtureProducts.Count)."

$searchRequest = @{
    query = "metro commute ANC over ear"
    mode = "rrf"
    page_size = 3
    filters = @{
        category = "over_ear"
        price_max = 1000
        currency = "CNY"
        anc = $true
    }
}
$searchFirst = Invoke-JsonRequest -Uri "$ApiBaseUrl/api/v1/search" -Method Post -Body $searchRequest
$searchSecond = Invoke-JsonRequest -Uri "$ApiBaseUrl/api/v1/search" -Method Post -Body $searchRequest
$searchItems = @($searchSecond.Data.items)
Assert-Stage9 ($searchSecond.StatusCode -eq 200 -and $searchItems.Count -gt 0) "Text search returned no products."
Assert-Stage9 ($searchSecond.Headers["X-ShopLens-Cache"] -eq "HIT") "The repeated search did not produce a cache HIT."
foreach ($item in $searchItems) {
    Assert-Stage9 ($item.product.category -eq "over_ear") "Search violated the category hard filter."
    Assert-Stage9 ([decimal]$item.product.price_amount -le 1000) "Search violated the price hard filter."
    Assert-Stage9 ($item.product.currency -eq "CNY") "Search violated the currency hard filter."
    Assert-Stage9 ($item.product.anc -eq $true) "Search violated the ANC hard filter."
}

$assistantRequest = @{
    message = "Recommend ANC over-ear headphones for a metro commute under CNY 1000"
    filters = @{
        category = "over_ear"
        price_max = 1000
        currency = "CNY"
        anc = $true
    }
}
$assistant = Invoke-JsonRequest -Uri "$ApiBaseUrl/api/v1/assistant/query" -Method Post -Body $assistantRequest
$recommendations = @($assistant.Data.recommendations)
$evidence = @($assistant.Data.evidence)
Assert-Stage9 ($assistant.StatusCode -eq 200 -and $assistant.Data.status -in @("completed", "degraded")) "Assistant did not complete."
Assert-Stage9 ($recommendations.Count -gt 0) "Assistant returned no structured recommendations."
Assert-Stage9 ($evidence.Count -gt 0) "Assistant returned no evidence."
Assert-Stage9 ($assistant.Data.trace.citation_validation.valid -eq $true) "Assistant citation validation failed."
Assert-Stage9 (@($assistant.Data.trace.tool_steps).Count -le 4) "Assistant exceeded the four-step tool bound."

$metrics = Invoke-WebRequest -UseBasicParsing -Uri "$ApiBaseUrl/metrics" -TimeoutSec 20
Assert-Stage9 ($metrics.StatusCode -eq 200 -and $metrics.Content -match "shoplens_http_requests_total") "Prometheus metrics are unavailable."

$web = Invoke-WebRequest -UseBasicParsing -Uri $WebBaseUrl -TimeoutSec 20
$openGraph = Invoke-WebRequest -UseBasicParsing -Uri "$WebBaseUrl/og.png" -TimeoutSec 20
Assert-Stage9 ($web.StatusCode -eq 200 -and $web.Content -match "ShopLens") "Web application is unavailable."
Assert-Stage9 ($openGraph.StatusCode -eq 200 -and $openGraph.Headers["Content-Type"] -match "image/png") "Open Graph image is unavailable."

$report = [ordered]@{
    schema_version = "stage9-fixture-smoke-v1"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    transport = "http"
    endpoints = [ordered]@{
        api = $ApiBaseUrl
        web = $WebBaseUrl
    }
    checks = [ordered]@{
        readiness = $ready.Data.status
        fixture_product_count = $fixtureProducts.Count
        total_product_count = $products.Data.total
        search_mode = $searchSecond.Data.retrieval_mode
        search_result_count = $searchItems.Count
        repeated_search_cache = $searchSecond.Headers["X-ShopLens-Cache"]
        assistant_status = $assistant.Data.status
        recommendation_count = $recommendations.Count
        evidence_count = $evidence.Count
        citation_validation = $assistant.Data.trace.citation_validation.valid
        tool_step_count = @($assistant.Data.trace.tool_steps).Count
        metrics_http_status = $metrics.StatusCode
        web_http_status = $web.StatusCode
        open_graph_http_status = $openGraph.StatusCode
    }
    samples = [ordered]@{
        search_source_ids = @($searchItems | ForEach-Object { $_.product.source_url })
        assistant_trace_id = $assistant.Data.trace_id
    }
    result = "passed"
}

if ($OutputPath) {
    $resolvedOutputPath = if ([System.IO.Path]::IsPathRooted($OutputPath)) {
        $OutputPath
    } else {
        Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path $OutputPath
    }
    $outputDirectory = Split-Path -Parent $resolvedOutputPath
    if (-not (Test-Path -LiteralPath $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory | Out-Null
    }
    $json = $report | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($resolvedOutputPath, $json, [System.Text.UTF8Encoding]::new($false))
}

$report | ConvertTo-Json -Depth 8
