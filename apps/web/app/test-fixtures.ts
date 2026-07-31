function product() {
  return {
    id: "11111111-1111-1111-1111-111111111111", title: "Auralis Metro ANC 40", brand: "Auralis", category: "over_ear",
    price_amount: "899.00", currency: "CNY", price_observed_at: "2026-07-20T00:00:00Z", wireless: true, anc: true,
    battery_hours: "40.00", weight_grams: "245.00", colors: ["黑色"], codecs: ["AAC"], water_resistance: null,
    source_name: "fixture", source_url: "https://fixtures.shoplens.local/products/fixture-001",
  };
}

export function searchResponse() {
  return {
    retrieval_mode: "hybrid_rerank", query: "Auralis Metro ANC 40", page: 1, page_size: 12, total: 1,
    items: [{ rank: 1, lexical_rank: 1, lexical_score: 1.25, dense_rank: 2, dense_score: 0.82, rrf_score: 0.0325, rerank_score: 0.91, document_version: "stage3-lexical-v1", product: product() }],
    trace: { parameters: { rrf_k: 60 }, models: { embedding: "fixture" }, degraded_reason: null, channels: { lexical: [{ rank: 1 }], dense: [{ rank: 2 }] }, fusion: [{ rank: 1 }], rerank: [{ rank_after: 1 }], latency_ms: { total: 4.5 } },
  };
}

export function uploadedAsset() {
  return { asset_id: "22222222-2222-2222-2222-222222222222", media_type: "image/webp", byte_size: 120, width: 20, height: 20, content_sha256: "a".repeat(64) };
}

export function agentResponse() {
  const item = product();
  const evidenceId = `fact:${item.id}:price_amount`;
  return {
    status: "completed", session_id: "22222222-2222-2222-2222-222222222222", answer: "找到 1 件满足当前硬条件的候选。",
    recommendations: [{ product: item, rank: 1, matched_requirements: [{ text: "价格 899.00 CNY, 不超过 1000 CNY", evidence_ids: [evidenceId] }], reasons: [], tradeoffs: [], evidence_ids: [evidenceId] }],
    comparison: null, applied_filters: { price_max: "1000", currency: "CNY", anc: true }, soft_preferences: ["适合通勤"], relaxed_preferences: [],
    evidence: [{ id: evidenceId, product_id: item.id, kind: "product_fact", field: "price_amount", value: "899.00", available: true, source_name: "fixture", source_url: item.source_url, observed_at: item.price_observed_at, excerpt: null, untrusted_content: false }],
    trace_id: "33333333-3333-3333-3333-333333333333", trace: { states: ["ParseRequest", "SearchCatalog", "GetProductDetail", "ValidateCitations"], parser_mode: "rules", tool_steps: [{ step: 1, tool: "search_catalog", status: "ok", latency_ms: 1 }], model_calls: [], citation_validation: { valid: true, checked_statement_count: 1, errors: [] }, degraded_reasons: [], total_latency_ms: 4 }, warnings: [],
  };
}
