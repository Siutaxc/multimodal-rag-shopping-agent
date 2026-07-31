"""Strict schemas shared by parsing, tools, sessions, traces, and HTTP responses."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.products import ProductSummary
from app.api.search import SearchFiltersInput


class AgentIntent(StrEnum):
    RECOMMEND = "recommend"
    SEARCH = "search"
    COMPARE = "compare"


class FilterField(StrEnum):
    CATEGORY = "category"
    BRAND = "brand"
    PRICE_MIN = "price_min"
    PRICE_MAX = "price_max"
    CURRENCY = "currency"
    WIRELESS = "wireless"
    ANC = "anc"
    BATTERY_HOURS_MIN = "battery_hours_min"
    WEIGHT_GRAMS_MAX = "weight_grams_max"
    COLOR = "color"
    CODEC = "codec"
    WATER_RESISTANCE = "water_resistance"


class ParsedTurn(BaseModel):
    """Validated output accepted from either a model provider or the rule fallback."""

    model_config = ConfigDict(extra="forbid")

    intent: AgentIntent = AgentIntent.RECOMMEND
    filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)
    clear_fields: list[FilterField] = Field(default_factory=list, max_length=len(FilterField))
    clear_all: bool = False
    clear_soft_preferences: bool = False
    soft_preferences: list[str] = Field(default_factory=list, max_length=12)
    referenced_product_ids: list[UUID] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def validate_referenced_products(self) -> "ParsedTurn":
        if len(self.referenced_product_ids) != len(set(self.referenced_product_ids)):
            raise ValueError("referenced_product_ids must be unique")
        return self


class SessionContext(BaseModel):
    """Opaque-session state; no content from another session is merged implicitly."""

    model_config = ConfigDict(extra="forbid")

    session_id: UUID
    filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)
    soft_preferences: list[str] = Field(default_factory=list, max_length=12)
    last_product_ids: list[UUID] = Field(default_factory=list, max_length=4)
    updated_at: datetime


class EvidenceItem(BaseModel):
    """One product fact or untrusted review excerpt with stable provenance."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=180)
    product_id: UUID
    kind: Literal["product_fact", "review"]
    field: str = Field(min_length=1, max_length=80)
    value: str | bool | list[str] | None = None
    available: bool = True
    source_name: str = Field(min_length=1, max_length=120)
    source_url: str | None = None
    observed_at: datetime | None = None
    excerpt: str | None = Field(default=None, max_length=4000)
    untrusted_content: bool = False


class GroundedStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    evidence_ids: list[str] = Field(min_length=1, max_length=8)


class Recommendation(BaseModel):
    """A card is always structured; the UI never parses products from answer prose."""

    model_config = ConfigDict(extra="forbid")

    product: ProductSummary
    rank: int = Field(ge=1, le=4)
    matched_requirements: list[GroundedStatement] = Field(default_factory=list)
    reasons: list[GroundedStatement] = Field(default_factory=list)
    tradeoffs: list[GroundedStatement] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class ComparisonValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    value: str | bool | list[str] | None
    evidence_id: str


class ComparisonRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    label: str
    values: list[ComparisonValue]


class ComparisonBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_ids: list[UUID] = Field(min_length=2, max_length=4)
    rows: list[ComparisonRow]


class PlannedRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UUID
    evidence_ids: list[str] = Field(min_length=1, max_length=8)


class AnswerPlan(BaseModel):
    """A model may select evidence, but cannot author price or parameter values."""

    model_config = ConfigDict(extra="forbid")

    recommendations: list[PlannedRecommendation] = Field(default_factory=list, max_length=4)


class ToolStepTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step: int = Field(ge=1, le=4)
    tool: Literal[
        "get_query_context",
        "search_catalog",
        "get_product_detail",
        "compare_products",
    ]
    status: Literal["ok", "error"]
    input: dict[str, Any]
    output: dict[str, Any]
    latency_ms: float = Field(ge=0)


class ModelCallTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: Literal["parse", "answer_plan"]
    model: str
    status: Literal["ok", "timeout", "error", "fallback"]
    latency_ms: float = Field(ge=0)


class CitationValidationTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    checked_statement_count: int = Field(ge=0)
    errors: list[str] = Field(default_factory=list)


class AgentTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: UUID
    session_id: UUID
    states: list[str]
    parser_mode: Literal["model", "rules"]
    parsed_turn: ParsedTurn
    effective_filters: SearchFiltersInput
    tool_steps: list[ToolStepTrace] = Field(max_length=4)
    model_calls: list[ModelCallTrace]
    citation_validation: CitationValidationTrace
    retrieval: dict[str, Any] | None = None
    degraded_reasons: list[str]
    total_latency_ms: float = Field(ge=0)


class AssistantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["completed", "needs_clarification", "degraded"]
    session_id: UUID
    answer: str
    recommendations: list[Recommendation]
    comparison: ComparisonBundle | None = None
    applied_filters: SearchFiltersInput
    soft_preferences: list[str]
    relaxed_preferences: list[str]
    evidence: list[EvidenceItem]
    trace_id: UUID
    trace: AgentTrace
    warnings: list[str]
