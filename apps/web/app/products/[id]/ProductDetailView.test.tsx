import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ProductDetailView from "./ProductDetailView";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ProductDetailView", () => {
  it("loads facts and preserves the original source link", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          id: "product-id",
          title: "MetroTone Buds N8",
          brand: "MetroTone",
          category: "in_ear",
          description: "小型入耳式主动降噪样例耳机。",
          price_amount: "499.00",
          currency: "CNY",
          price_observed_at: "2026-07-20T00:00:00Z",
          wireless: true,
          anc: true,
          battery_hours: "8.00",
          weight_grams: "5.20",
          colors: ["黑色", "白色"],
          codecs: ["AAC", "SBC"],
          water_resistance: "IP54",
          microphone: "每侧双麦克风",
          source_name: "fixture",
          source_id: "fixture-003",
          source_version: "v1",
          transformation_version: "stage2-v1",
          source_url: "https://fixtures.shoplens.local/products/fixture-003",
          review_evidence: [],
        }),
      }),
    );

    render(<ProductDetailView productId="product-id" />);

    expect(await screen.findByRole("heading", { name: "MetroTone Buds N8" })).toBeInTheDocument();
    expect(screen.getByText("每侧双麦克风")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "打开原始来源 ↗" })).toHaveAttribute(
      "href",
      "https://fixtures.shoplens.local/products/fixture-003",
    );
  });
});
