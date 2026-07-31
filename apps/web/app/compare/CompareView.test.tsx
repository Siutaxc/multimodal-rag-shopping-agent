import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import CompareView from "./CompareView";

beforeEach(() => window.localStorage.clear());
afterEach(() => vi.unstubAllGlobals());

describe("CompareView", () => {
  it("renders a semantic table and evidence links for two products", async () => {
    const products = [summary("p-1", "Auralis Metro ANC 40", "899.00"), summary("p-2", "QuietArc Studio Q2", "799.00")];
    window.localStorage.setItem("shoplens:stage7:comparison", JSON.stringify(products));
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => comparisonResponse(products) }));

    render(<CompareView />);

    const table = await screen.findByRole("table", { name: "ShopLens 商品结构化事实对比" });
    expect(table).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: /Auralis Metro ANC 40/ })).toBeInTheDocument();
    expect(screen.getByRole("rowheader", { name: "价格" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "核验单元格 →" })[0]).toHaveAttribute("href", "/products/p-1#fact-price-amount");
  });
});

function summary(id: string, title: string, price: string) {
  return { id, title, brand: title.split(" ")[0], category: "over_ear", price_amount: price, currency: "CNY", price_observed_at: "2026-07-20T00:00:00Z", wireless: true, anc: true, battery_hours: "40.00", weight_grams: "245.00", colors: ["黑色"], codecs: ["AAC"], water_resistance: null, source_name: "fixture", source_url: `https://example.test/${id}` };
}

function comparisonResponse(products: ReturnType<typeof summary>[]) {
  const evidence = products.map((product) => ({ id: `fact:${product.id}:price_amount`, product_id: product.id, kind: "product_fact", field: "price_amount", value: product.price_amount, available: true, source_name: "fixture", source_url: product.source_url, observed_at: product.price_observed_at, excerpt: null, untrusted_content: false }));
  return {
    status: "completed", session_id: "session", answer: "对比 2 件商品。", recommendations: [],
    comparison: { product_ids: products.map((product) => product.id), rows: [{ field: "price_amount", label: "价格", values: products.map((product) => ({ product_id: product.id, value: product.price_amount, evidence_id: `fact:${product.id}:price_amount` })) }] },
    applied_filters: {}, soft_preferences: [], relaxed_preferences: [], evidence, trace_id: "trace", warnings: [],
    trace: { states: ["CompareProducts"], parser_mode: "rules", tool_steps: [{ step: 1, tool: "compare_products", status: "ok", latency_ms: 1 }], model_calls: [], citation_validation: { valid: true, checked_statement_count: 2, errors: [] }, degraded_reasons: [], total_latency_ms: 2 },
  };
}
