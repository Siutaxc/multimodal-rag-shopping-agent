import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Home from "./page";
import { agentResponse, searchResponse, uploadedAsset } from "./test-fixtures";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

beforeEach(() => {
  window.localStorage.clear();
  pushMock.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Home", () => {
  it("submits hybrid text and hard filters, stores structured results, then opens results", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => searchResponse(),
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<Home />);

    fireEvent.click(screen.getByRole("radio", { name: "纯文本" }));
    fireEvent.change(screen.getByLabelText("搜索词"), { target: { value: "Auralis Metro ANC 40" } });
    fireEvent.change(screen.getByLabelText("类型"), { target: { value: "over_ear" } });
    fireEvent.change(screen.getByLabelText("最高价格"), { target: { value: "1000" } });
    fireEvent.change(screen.getByLabelText("主动降噪"), { target: { value: "true" } });
    fireEvent.click(screen.getByRole("button", { name: "开始检索" }));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/results"));
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8000/api/v1/search");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({
      query: "Auralis Metro ANC 40",
      mode: "rerank",
      page: 1,
      page_size: 12,
      filters: { category: "over_ear", price_max: "1000", anc: true },
    });
    expect(JSON.parse(window.localStorage.getItem("shoplens:stage7:snapshot") ?? "null").results.total).toBe(1);
  });

  it("announces an HTTP failure without navigating", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({ detail: "not ready" }) }));
    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: "开始导购" }));

    expect(await screen.findByRole("status")).toHaveTextContent("HTTP 503：not ready");
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("validates and deletes a local image preview", async () => {
    const createObjectURL = vi.fn().mockReturnValue("blob:preview");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });
    render(<Home />);

    const file = new File(["pixels"], "reference.png", { type: "image/png" });
    fireEvent.change(screen.getByLabelText("参考图片"), { target: { files: [file] } });
    expect(screen.getByAltText("参考图片预览：reference.png")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "删除图片" }));
    expect(screen.queryByAltText("参考图片预览：reference.png")).not.toBeInTheDocument();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:preview");
  });

  it("uploads a raster asset before agent search and persists only the opaque session locally", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, status: 201, json: async () => uploadedAsset() })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => agentResponse() });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("URL", { createObjectURL: vi.fn().mockReturnValue("blob:preview"), revokeObjectURL: vi.fn() });
    render(<Home />);

    const file = new File(["pixels"], "reference.png", { type: "image/png" });
    fireEvent.change(screen.getByLabelText("参考图片"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "开始导购" }));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/results"));
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8000/api/v1/assets/images");
    expect(JSON.parse(fetchMock.mock.calls[1][1].body as string)).toMatchObject({ asset_id: uploadedAsset().asset_id });
    expect(JSON.parse(window.localStorage.getItem("shoplens:stage7:session") ?? "null")).toBe(agentResponse().session_id);
    expect(pushMock.mock.calls[0][0]).not.toContain(agentResponse().session_id);
  });
});
