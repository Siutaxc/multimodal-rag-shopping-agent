export type ProductSummary = {
  id: string;
  title: string;
  brand: string;
  category: string;
  price_amount: string;
  currency: string;
  price_observed_at: string;
  wireless: boolean | null;
  anc: boolean | null;
  battery_hours: string | null;
  weight_grams: string | null;
  colors: string[];
  codecs: string[];
  water_resistance: string | null;
  source_name: string;
  source_url: string;
};

export type ProductDetail = ProductSummary & {
  description: string | null;
  microphone: string | null;
  source_id: string;
  source_version: string;
  transformation_version: string;
  images: Array<{
    id: string;
    position: number;
    storage_key: string;
    source_url: string | null;
    sha256: string;
    media_type: string;
    byte_size: number;
    width: number | null;
    height: number | null;
    alt_text: string | null;
  }>;
  review_evidence: Array<{
    id: string;
    source_name: string;
    source_review_id: string;
    topic: string;
    excerpt: string;
    rating: string | null;
    reviewed_at: string | null;
    source_url: string | null;
  }>;
  created_at: string;
  updated_at: string;
};

export type HardFilters = {
  category?: string;
  brand?: string;
  price_min?: string;
  price_max?: string;
  currency?: string;
  wireless?: boolean;
  anc?: boolean;
  battery_hours_min?: string;
  weight_grams_max?: string;
  color?: string;
  codec?: string;
  water_resistance?: string;
};

export type FilterField = keyof HardFilters;

export type SearchKind = "agent" | "text" | "image" | "multimodal";

export type SearchDraft = {
  query: string;
  searchKind: SearchKind;
  mode: "rerank" | "rrf" | "dense" | "lexical";
  category: string;
  priceMax: string;
  anc: "" | "true" | "false";
};

export type SearchResponse = {
  retrieval_mode:
    | "postgresql_lexical"
    | "pgvector_dense"
    | "hybrid_rrf"
    | "hybrid_rerank"
    | "hybrid_rrf_fallback"
    | "pgvector_image"
    | "multimodal_rrf"
    | "multimodal_text_fallback"
    | "image_unavailable";
  query: string | null;
  items: Array<{
    rank: number;
    lexical_rank: number | null;
    lexical_score: number | null;
    dense_rank: number | null;
    dense_score: number | null;
    rrf_score: number | null;
    rerank_score: number | null;
    text_rank?: number | null;
    text_rrf_score?: number | null;
    image_rank?: number | null;
    image_score?: number | null;
    matched_image_id?: string | null;
    fusion_score?: number | null;
    document_version: string;
    product: ProductSummary;
  }>;
  page: number;
  page_size: number;
  total: number;
  trace: {
    parameters: Record<string, number>;
    models: Record<string, string>;
    degraded_reason: string | null;
    channels: Record<string, Array<Record<string, string | number | null>>>;
    fusion?: Array<Record<string, string | number | null>>;
    rerank?: Array<Record<string, string | number | null>>;
    text_trace?: {
      channels: Record<string, Array<Record<string, string | number | null>>>;
      fusion: Array<Record<string, string | number | null>>;
      rerank: Array<Record<string, string | number | null>>;
      latency_ms: Record<string, number>;
    };
    latency_ms: Record<string, number>;
  };
};

export type UploadedImageAsset = {
  asset_id: string;
  media_type: string;
  byte_size: number;
  width: number;
  height: number;
  content_sha256: string;
};

export type AgentEvidence = {
  id: string;
  product_id: string;
  kind: "product_fact" | "review";
  field: string;
  value: string | boolean | string[] | null;
  available: boolean;
  source_name: string;
  source_url: string | null;
  observed_at: string | null;
  excerpt: string | null;
  untrusted_content: boolean;
};

export type GroundedStatement = {
  text: string;
  evidence_ids: string[];
};

export type AssistantResponse = {
  status: "completed" | "needs_clarification" | "degraded";
  session_id: string;
  answer: string;
  recommendations: Array<{
    product: ProductSummary;
    rank: number;
    matched_requirements: GroundedStatement[];
    reasons: GroundedStatement[];
    tradeoffs: GroundedStatement[];
    evidence_ids: string[];
  }>;
  comparison: {
    product_ids: string[];
    rows: Array<{
      field: string;
      label: string;
      values: Array<{
        product_id: string;
        value: string | boolean | string[] | null;
        evidence_id: string;
      }>;
    }>;
  } | null;
  applied_filters: Record<string, string | boolean | null>;
  soft_preferences: string[];
  relaxed_preferences: string[];
  evidence: AgentEvidence[];
  trace_id: string;
  trace: {
    states: string[];
    parser_mode: "model" | "rules";
    tool_steps: Array<{
      step: number;
      tool: string;
      status: "ok" | "error";
      latency_ms: number;
    }>;
    model_calls: Array<{
      phase: string;
      model: string;
      status: string;
      latency_ms: number;
    }>;
    citation_validation: {
      valid: boolean;
      checked_statement_count: number;
      errors: string[];
    };
    degraded_reasons: string[];
    total_latency_ms: number;
  };
  warnings: string[];
};

export type SessionContext = {
  session_id: string;
  filters: Record<string, string | boolean | null>;
  soft_preferences: string[];
  last_product_ids: string[];
  updated_at: string;
};

export type AgentTraceDetail = Omit<AssistantResponse["trace"], "tool_steps"> & {
  trace_id: string;
  session_id: string;
  parsed_turn: Record<string, unknown>;
  effective_filters: Record<string, string | boolean | null>;
  retrieval: Record<string, unknown> | null;
  tool_steps: Array<AssistantResponse["trace"]["tool_steps"][number] & {
    input: Record<string, unknown>;
    output: Record<string, unknown>;
  }>;
};

export function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_SHOPLENS_API_BASE_URL ?? "http://localhost:8000";
}
