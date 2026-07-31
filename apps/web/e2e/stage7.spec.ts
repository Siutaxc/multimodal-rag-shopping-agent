import { expect, type Page, test } from "@playwright/test";
import path from "node:path";

const first = product("11111111-1111-1111-1111-111111111111", "Auralis Metro ANC 40", "899.00");
const second = product("22222222-2222-2222-2222-222222222222", "QuietArc Studio Q2", "799.00");

test.beforeEach(async ({ page }) => {
  await installFixtureApi(page);
});

test("文本查询后打开商品详情并定位事实", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("radio", { name: "纯文本" }).check();
  await page.getByLabel("搜索词").fill("通勤降噪，戴眼镜舒适");
  await page.getByRole("button", { name: "开始检索" }).click();

  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("heading", { name: first.title })).toBeVisible();
  await page.getByRole("link", { name: "查看事实与来源 →" }).first().click();
  await expect(page).toHaveURL(new RegExp(`/products/${first.id}$`));
  await expect(page.getByRole("heading", { name: first.title })).toBeVisible();
  await expect(page.getByText("价格观测时间")).toBeVisible();
  await expect(page.getByRole("link", { name: "打开原始来源 ↗" })).toBeVisible();
});

test("纯图片与图文输入均可提交，图文结果保持预算硬条件", async ({ page }) => {
  const fixture = path.resolve(process.cwd(), "../../data/fixtures/images/fixture-001.png");
  await page.goto("/");
  await page.getByRole("radio", { name: "纯图片" }).check();
  await page.getByLabel("参考图片").setInputFiles(fixture);
  await expect(page.getByAltText(/参考图片预览/)).toBeVisible();
  await page.getByRole("button", { name: "开始检索" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("heading", { name: first.title })).toBeVisible();

  await page.goto("/");
  await page.getByRole("radio", { name: "图片 + 文字" }).check();
  await page.getByLabel("搜索词").fill("找外观相近的黑色款，预算 800 元");
  await page.getByLabel("最高价格").fill("800");
  await page.getByLabel("参考图片").setInputFiles(fixture);
  await page.getByRole("button", { name: "开始检索" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("heading", { name: second.title })).toBeVisible();
  await expect(page.getByText("799.00")).toBeVisible();
  await expect(page.getByText("899.00")).toHaveCount(0);
});

test("选择两件商品完成语义表格对比", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("radio", { name: "纯文本" }).check();
  await page.getByRole("button", { name: "开始检索" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await page.getByRole("button", { name: "加入对比", exact: true }).first().click();
  await page.getByRole("button", { name: "加入对比", exact: true }).first().click();
  await page.getByRole("link", { name: "对比 2 件商品" }).click();

  await expect(page).toHaveURL(/\/compare$/);
  await expect(page.getByRole("table", { name: "ShopLens 商品结构化事实对比" })).toBeVisible();
  await expect(page.getByRole("rowheader", { name: "价格" })).toBeVisible();
  await expect(page.getByRole("link", { name: "核验单元格 →" }).first()).toBeVisible();
});

test("追问修改预算后恢复同一会话并展示新条件", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("搜索词").fill("1000 元以内，头戴式，主动降噪");
  await page.getByRole("button", { name: "开始导购" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("button", { name: "清除条件：最高价格" })).toContainText("1000");

  await page.getByLabel("搜索词").fill("预算改为 800 元，其他条件不变");
  await page.getByRole("spinbutton", { name: "最高价格" }).fill("800");
  await page.getByRole("button", { name: "开始导购" }).click();
  await expect(page.getByRole("button", { name: "清除条件：最高价格" })).toContainText("800");
  await page.reload();
  await expect(page.getByText(/会话已恢复/)).toBeVisible();
  await expect(page.getByRole("button", { name: "清除条件：最高价格" })).toContainText("800");
});

test("Reranker 故障时明确展示确定性降级结果", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("radio", { name: "纯文本" }).check();
  await page.getByLabel("搜索词").fill("触发重排降级");
  await page.getByRole("button", { name: "开始检索" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await expect(page.getByRole("status")).toContainText("部分能力发生降级");
  await page.getByText(/检索轨迹 · hybrid_rrf_fallback/).click();
  await expect(page.getByText("部分降级：reranker_timeout")).toBeVisible();
  await expect(page.getByRole("heading", { name: first.title })).toBeVisible();
});

async function installFixtureApi(page: Page) {
  let agentTurn = 0;
  await page.route("http://localhost:8000/api/v1/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    if (pathname === "/api/v1/assets/images") return json(route, uploadedAsset(), 201);
    if (pathname === "/api/v1/search") {
      const body = request.postDataJSON() as { query: string };
      return json(route, searchResponse(body.query.includes("触发重排降级")));
    }
    if (pathname === "/api/v1/multimodal-search") {
      const body = request.postDataJSON() as { filters?: { price_max?: string } };
      return json(route, searchResponse(false, body.filters?.price_max === "800" ? [second] : [first]));
    }
    if (pathname === "/api/v1/assistant/query") {
      agentTurn += 1;
      const body = request.postDataJSON() as { filters?: { price_max?: string } };
      return json(route, agentResponse(body.filters?.price_max ?? (agentTurn > 1 ? "800" : "1000")));
    }
    if (pathname === "/api/v1/products/compare") return json(route, comparisonResponse());
    if (pathname.startsWith("/api/v1/sessions/")) return json(route, { session_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", filters: { price_max: "800", currency: "CNY", anc: true }, soft_preferences: [], last_product_ids: [second.id], updated_at: "2026-07-22T00:00:00Z" });
    if (pathname.startsWith("/api/v1/products/")) {
      const match = [first, second].find((item) => pathname.endsWith(item.id)) ?? first;
      return json(route, detail(match));
    }
    return route.abort();
  });
}

function product(id: string, title: string, price: string) {
  return { id, title, brand: title.split(" ")[0], category: "over_ear", price_amount: price, currency: "CNY", price_observed_at: "2026-07-20T00:00:00Z", wireless: true, anc: true, battery_hours: "40.00", weight_grams: "245.00", colors: ["黑色"], codecs: ["AAC"], water_resistance: null, source_name: "fixture", source_url: `https://fixtures.shoplens.local/${id}` };
}

function searchResponse(degraded = false, products = [first, second]) {
  return { retrieval_mode: degraded ? "hybrid_rrf_fallback" : "hybrid_rerank", query: "fixture", page: 1, page_size: 12, total: products.length, items: products.map((item, index) => ({ rank: index + 1, lexical_rank: index + 1, lexical_score: 1 - index * 0.1, dense_rank: index + 1, dense_score: 0.9 - index * 0.1, rrf_score: 0.03, rerank_score: degraded ? null : 0.9, document_version: "stage3-lexical-v1", product: item })), trace: { parameters: { rrf_k: 60 }, models: { embedding: "fixture" }, degraded_reason: degraded ? "reranker_timeout" : null, channels: { lexical: [{ rank: 1 }], dense: [{ rank: 1 }] }, fusion: [{ rank: 1 }], rerank: degraded ? [] : [{ rank_after: 1 }], latency_ms: { total: 5 } } };
}

function agentResponse(priceMax: string) {
  const item = priceMax === "800" ? second : first;
  const evidenceId = `fact:${item.id}:price_amount`;
  return { status: "completed", session_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", answer: "已按当前硬条件返回可核验候选。", recommendations: [{ product: item, rank: 1, matched_requirements: [{ text: `价格 ${item.price_amount} CNY，不超过 ${priceMax} CNY`, evidence_ids: [evidenceId] }], reasons: [], tradeoffs: [], evidence_ids: [evidenceId] }], comparison: null, applied_filters: { price_max: priceMax, currency: "CNY", anc: true }, soft_preferences: ["通勤"], relaxed_preferences: [], evidence: [{ id: evidenceId, product_id: item.id, kind: "product_fact", field: "price_amount", value: item.price_amount, available: true, source_name: "fixture", source_url: item.source_url, observed_at: item.price_observed_at, excerpt: null, untrusted_content: false }], trace_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", trace: { states: ["ParseRequest", "SearchCatalog", "GetProductDetail", "ValidateCitations"], parser_mode: "rules", tool_steps: [{ step: 1, tool: "search_catalog", status: "ok", latency_ms: 1 }], model_calls: [], citation_validation: { valid: true, checked_statement_count: 1, errors: [] }, degraded_reasons: [], total_latency_ms: 4 }, warnings: [] };
}

function comparisonResponse() {
  const items = [first, second];
  return { ...agentResponse("1000"), recommendations: [], comparison: { product_ids: items.map((item) => item.id), rows: [{ field: "price_amount", label: "价格", values: items.map((item) => ({ product_id: item.id, value: item.price_amount, evidence_id: `fact:${item.id}:price_amount` })) }] }, evidence: items.map((item) => ({ id: `fact:${item.id}:price_amount`, product_id: item.id, kind: "product_fact", field: "price_amount", value: item.price_amount, available: true, source_name: "fixture", source_url: item.source_url, observed_at: item.price_observed_at, excerpt: null, untrusted_content: false })) };
}

function uploadedAsset() { return { asset_id: "cccccccc-cccc-cccc-cccc-cccccccccccc", media_type: "image/webp", byte_size: 120, width: 20, height: 20, content_sha256: "a".repeat(64) }; }
function detail(item: typeof first) { return { ...item, description: "可核验的合成 Fixture 商品描述。", microphone: "双麦克风", source_id: item.id, source_version: "v1", transformation_version: "stage2-v1", images: [], review_evidence: [], created_at: "2026-07-20T00:00:00Z", updated_at: "2026-07-20T00:00:00Z" }; }
function json(route: Parameters<Parameters<Page["route"]>[1]>[0], body: unknown, status = 200) { return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) }); }
