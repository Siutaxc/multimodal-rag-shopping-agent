import { afterEach, describe, expect, it, vi } from "vitest";

import { requestJson } from "./shoplens-client";

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("requestJson", () => {
  it("turns an aborted HTTP request into a clear timeout state", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn((_url: string, init?: RequestInit) => new Promise((_resolve, reject) => {
      init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
    })));

    const request = requestJson("http://localhost:8000/slow", undefined, 25);
    const assertion = expect(request).rejects.toMatchObject({ kind: "timeout", message: "请求超时，请重试或改用确定性检索" });
    await vi.advanceTimersByTimeAsync(25);
    await assertion;
  });
});
