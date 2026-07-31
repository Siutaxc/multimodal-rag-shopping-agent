import type {
  AssistantResponse,
  FilterField,
  HardFilters,
  ProductSummary,
  SearchDraft,
  SearchResponse,
  UploadedImageAsset,
} from "./product-types";
import { apiBaseUrl } from "./product-types";

export const DEFAULT_DRAFT: SearchDraft = {
  query: "1000 元以内，头戴式，地铁通勤，降噪强，戴眼镜尽量舒服。",
  searchKind: "agent",
  mode: "rerank",
  category: "",
  priceMax: "",
  anc: "",
};

export const STORAGE_KEYS = {
  snapshot: "shoplens:stage7:snapshot",
  session: "shoplens:stage7:session",
  comparison: "shoplens:stage7:comparison",
} as const;

export type SearchSnapshot = {
  draft: SearchDraft;
  agentResults: AssistantResponse | null;
  results: SearchResponse | null;
  savedAt: string;
};

export type SearchExecution = {
  agentResults: AssistantResponse | null;
  results: SearchResponse | null;
  uploadedAsset: UploadedImageAsset | null;
};

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public readonly status: number | null = null,
    public readonly kind: "http" | "timeout" | "network" = "http",
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

export function buildHardFilters(draft: SearchDraft): HardFilters {
  const filters: HardFilters = {};
  if (draft.category) filters.category = draft.category;
  if (draft.priceMax) filters.price_max = draft.priceMax;
  if (draft.anc) filters.anc = draft.anc === "true";
  return filters;
}

export async function requestJson<T>(
  url: string,
  init?: RequestInit,
  timeoutMs = 12_000,
): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    if (!response.ok) {
      let detail = "";
      try {
        const body = (await response.json()) as { detail?: string };
        detail = body.detail ? `：${body.detail}` : "";
      } catch {
        // The status is still useful when an upstream proxy returns non-JSON.
      }
      throw new ApiRequestError(`HTTP ${response.status}${detail}`, response.status);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiRequestError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiRequestError("请求超时，请重试或改用确定性检索", null, "timeout");
    }
    throw new ApiRequestError(
      error instanceof Error ? error.message : "无法连接服务",
      null,
      "network",
    );
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function executeSearch({
  draft,
  image,
  sessionId,
  clearFields = [],
}: {
  draft: SearchDraft;
  image: File | null;
  sessionId: string | null;
  clearFields?: FilterField[];
}): Promise<SearchExecution> {
  const filters = buildHardFilters(draft);
  let uploadedAsset: UploadedImageAsset | null = null;

  if (image && draft.searchKind !== "text") {
    uploadedAsset = await requestJson<UploadedImageAsset>(
      `${apiBaseUrl()}/api/v1/assets/images`,
      {
        method: "POST",
        headers: { "Content-Type": image.type },
        body: image,
      },
      15_000,
    );
  }

  if (draft.searchKind === "agent") {
    const agentResults = await requestJson<AssistantResponse>(
      `${apiBaseUrl()}/api/v1/assistant/query`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: draft.query,
          session_id: sessionId ?? undefined,
          asset_id: uploadedAsset?.asset_id,
          filters,
          clear_fields: clearFields,
        }),
      },
    );
    return { agentResults, results: null, uploadedAsset };
  }

  if (draft.searchKind === "text") {
    const results = await requestJson<SearchResponse>(`${apiBaseUrl()}/api/v1/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: draft.query,
        mode: draft.mode,
        page: 1,
        page_size: 12,
        filters,
      }),
    });
    return { agentResults: null, results, uploadedAsset };
  }

  const results = await requestJson<SearchResponse>(
    `${apiBaseUrl()}/api/v1/multimodal-search`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        asset_id: uploadedAsset?.asset_id,
        query: draft.searchKind === "multimodal" ? draft.query : undefined,
        page: 1,
        page_size: 12,
        filters,
      }),
    },
  );
  return { agentResults: null, results, uploadedAsset };
}

export function readLocalValue<T>(key: string): T | null {
  if (typeof window === "undefined") return null;
  try {
    const value = window.localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : null;
  } catch {
    return null;
  }
}

export function writeLocalValue<T>(key: string, value: T): void {
  window.localStorage.setItem(key, JSON.stringify(value));
}

export function removeLocalValue(key: string): void {
  window.localStorage.removeItem(key);
}

export function saveSearchExecution(draft: SearchDraft, execution: SearchExecution): SearchSnapshot {
  const snapshot: SearchSnapshot = {
    draft,
    agentResults: execution.agentResults,
    results: execution.results,
    savedAt: new Date().toISOString(),
  };
  writeLocalValue(STORAGE_KEYS.snapshot, snapshot);
  if (execution.agentResults) {
    writeLocalValue(STORAGE_KEYS.session, execution.agentResults.session_id);
  }
  return snapshot;
}

export function readComparison(): ProductSummary[] {
  return readLocalValue<ProductSummary[]>(STORAGE_KEYS.comparison) ?? [];
}

export function writeComparison(products: ProductSummary[]): void {
  writeLocalValue(STORAGE_KEYS.comparison, products.slice(0, 4));
  window.dispatchEvent(new Event("shoplens:comparison"));
}

export function evidenceAnchor(kind: "product_fact" | "review", field: string, id: string): string {
  if (kind === "product_fact") return `fact-${field.replaceAll("_", "-")}`;
  return `review-${id.split(":").at(-1)?.replace(/[^a-zA-Z0-9-]/g, "-") ?? "evidence"}`;
}
