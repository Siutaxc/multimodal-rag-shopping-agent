import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { agentResponse } from "../test-fixtures";
import ResultsView from "./ResultsView";

beforeEach(() => {
  window.localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ResultsView", () => {
  it("restores structured results, locates evidence, edits conditions, and manages comparison", async () => {
    const payload = agentResponse();
    window.localStorage.setItem("shoplens:stage7:snapshot", JSON.stringify({
      draft: { query: "预算 1000 元，主动降噪", searchKind: "agent", mode: "rerank", category: "", priceMax: "1000", anc: "true" },
      agentResults: payload,
      results: null,
      savedAt: "2026-07-22T00:00:00Z",
    }));
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ ...payload, applied_filters: { currency: "CNY", anc: true } }) });
    vi.stubGlobal("fetch", fetchMock);

    render(<ResultsView />);

    expect(await screen.findByRole("heading", { name: "Auralis Metro ANC 40" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "定位证据" })).toHaveAttribute("href", `/products/${payload.recommendations[0].product.id}#fact-price-amount`);

    fireEvent.click(screen.getByRole("button", { name: "加入对比" }));
    expect(screen.getByRole("complementary", { name: "商品对比栏" })).toBeInTheDocument();
    expect(JSON.parse(window.localStorage.getItem("shoplens:stage7:comparison") ?? "[]")).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "清除条件：最高价格" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toMatchObject({ clear_fields: ["price_max"] });
  });

  it("shows an explicit recovery action for an empty result", async () => {
    const payload = { ...agentResponse(), recommendations: [], answer: "没有满足条件的商品。" };
    window.localStorage.setItem("shoplens:stage7:snapshot", JSON.stringify({
      draft: { query: "预算 1 元", searchKind: "agent", mode: "rerank", category: "", priceMax: "1", anc: "" },
      agentResults: payload,
      results: null,
      savedAt: "2026-07-22T00:00:00Z",
    }));
    render(<ResultsView />);
    expect(await screen.findByRole("button", { name: "清除硬条件并重试" })).toBeInTheDocument();
    expect(screen.getByText("没有商品同时满足这些条件")).toBeInTheDocument();
  });
});
