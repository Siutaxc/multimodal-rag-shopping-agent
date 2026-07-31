"""Finite shopping-agent state machine with explicit degradation and trace."""

from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, TypeVar
from uuid import UUID, uuid4

from app.agent.evidence import (
    build_comparison,
    build_evidence,
    build_recommendations,
    safe_answer_text,
    validate_citations,
)
from app.agent.parsing import RuleConstraintParser, merge_session_context
from app.agent.schemas import (
    AgentIntent,
    AgentTrace,
    AnswerPlan,
    AssistantResponse,
    CitationValidationTrace,
    FilterField,
    ModelCallTrace,
    ParsedTurn,
    PlannedRecommendation,
    SessionContext,
    ToolStepTrace,
)
from app.agent.state import AgentStateStore, StateStoreError
from app.agent.tools import AgentToolbox, CatalogToolResult
from app.api.search import SearchFiltersInput
from app.core.settings import Settings
from app.db.models import Product
from app.db.products import ProductFilters
from app.providers.agent import AgentModelProvider
from app.providers.retrieval import (
    ProviderCircuitOpenError,
    ProviderError,
    ProviderTimeoutError,
)

T = TypeVar("T")


class ToolStepLimitError(RuntimeError):
    """No fifth tool call is ever attempted."""


class _ToolBudget:
    def __init__(self, maximum: int) -> None:
        self._maximum = maximum
        self.steps: list[ToolStepTrace] = []

    def call(
        self,
        name: str,
        input_summary: dict[str, Any],
        function: Callable[[], T],
        output_summary: Callable[[T], dict[str, Any]],
    ) -> T:
        if len(self.steps) >= self._maximum:
            raise ToolStepLimitError("agent tool step limit reached")
        started = perf_counter()
        step = len(self.steps) + 1
        try:
            value = function()
        except Exception as error:
            self.steps.append(
                ToolStepTrace(
                    step=step,
                    tool=name,
                    status="error",
                    input=input_summary,
                    output={"error_type": type(error).__name__},
                    latency_ms=_elapsed_ms(started),
                )
            )
            raise
        self.steps.append(
            ToolStepTrace(
                step=step,
                tool=name,
                status="ok",
                input=input_summary,
                output=output_summary(value),
                latency_ms=_elapsed_ms(started),
            )
        )
        return value


class BoundedShoppingAgent:
    """Tool policy is fixed in code; the model only parses schemas and selects evidence."""

    def __init__(
        self,
        tools: AgentToolbox,
        state: AgentStateStore,
        model: AgentModelProvider,
        settings: Settings,
    ) -> None:
        self._tools = tools
        self._state = state
        self._model = model
        self._settings = settings
        self._rules = RuleConstraintParser()

    def query(
        self,
        message: str,
        *,
        session_id: UUID | None = None,
        asset_id: UUID | None = None,
        explicit_filters: SearchFiltersInput | None = None,
        clear_fields: list[FilterField] | None = None,
        product_ids: list[UUID] | None = None,
    ) -> AssistantResponse:
        started = perf_counter()
        resolved_session_id = session_id or uuid4()
        trace_id = uuid4()
        states = ["ParseRequest"]
        degraded: list[str] = []
        warnings = ["价格来自带时间戳的数据快照, 请以下单页为准。"]
        budget = _ToolBudget(self._settings.agent_max_tool_steps)
        model_calls: list[ModelCallTrace] = []

        context: SessionContext | None = None
        if session_id is not None:
            states.append("GetQueryContext")
            try:
                context = budget.call(
                    "get_query_context",
                    {"session_id": str(session_id)},
                    lambda: self._state.get_session(session_id),
                    lambda value: {"found": value is not None},
                )
            except StateStoreError:
                degraded.append("session_store_unavailable")
                warnings.append("会话存储暂不可用, 本轮未继承历史条件。")

        parse_started = perf_counter()
        parser_mode = "model"
        try:
            turn = self._model.parse_request(
                message,
                context.filters if context is not None else SearchFiltersInput(),
            )
            model_calls.append(
                ModelCallTrace(
                    phase="parse",
                    model=self._model.identity,
                    status="ok",
                    latency_ms=_elapsed_ms(parse_started),
                )
            )
        except ProviderCircuitOpenError:
            parser_mode = "rules"
            turn = self._rules.parse(message)
            degraded.append("agent_parse_circuit_open")
            model_calls.append(
                ModelCallTrace(
                    phase="parse",
                    model=self._model.identity,
                    status="error",
                    latency_ms=_elapsed_ms(parse_started),
                )
            )
        except ProviderTimeoutError:
            parser_mode = "rules"
            turn = self._rules.parse(message)
            degraded.append("agent_parse_timeout")
            model_calls.append(
                ModelCallTrace(
                    phase="parse",
                    model=self._model.identity,
                    status="timeout",
                    latency_ms=_elapsed_ms(parse_started),
                )
            )
        except (ProviderError, ValueError):
            parser_mode = "rules"
            turn = self._rules.parse(message)
            degraded.append("agent_parse_error")
            model_calls.append(
                ModelCallTrace(
                    phase="parse",
                    model=self._model.identity,
                    status="error",
                    latency_ms=_elapsed_ms(parse_started),
                )
            )
        if product_ids:
            turn = turn.model_copy(update={"referenced_product_ids": product_ids})
        filters, soft_preferences = merge_session_context(
            context,
            turn,
            explicit_filters=explicit_filters,
            explicit_clear_fields=clear_fields,
        )

        if _needs_clarification(turn, filters, soft_preferences, asset_id):
            states.append("NeedClarification")
            return self._finalize_clarification(
                resolved_session_id,
                trace_id,
                turn,
                filters,
                soft_preferences,
                states,
                parser_mode,
                budget,
                model_calls,
                degraded,
                warnings,
                started,
            )

        retrieval_trace: dict[str, Any] | None = None
        products: list[Product] = []
        comparison = None
        referenced_ids = list(turn.referenced_product_ids)
        if turn.intent == AgentIntent.COMPARE and 2 <= len(referenced_ids) <= 4:
            states.append("CompareProducts")
            products = self._call_products_tool(
                budget,
                "compare_products",
                referenced_ids,
                self._tools.compare_products,
                degraded,
            )
        else:
            states.append("SearchCatalog")
            effective_query = _effective_query(message, soft_preferences)
            catalog: CatalogToolResult | None = None
            try:
                catalog = budget.call(
                    "search_catalog",
                    {
                        "query": effective_query,
                        "filters": filters.model_dump(mode="json", exclude_none=True),
                        "asset_id": str(asset_id) if asset_id is not None else None,
                    },
                    lambda: self._tools.search_catalog(
                        effective_query,
                        _product_filters(filters),
                        asset_id=asset_id,
                    ),
                    lambda value: {
                        "mode": value.mode,
                        "candidate_count": len(value.candidates),
                        "total": value.total,
                    },
                )
            except ToolStepLimitError:
                degraded.append("tool_step_limit")
            if catalog is not None:
                retrieval_trace = catalog.trace
                reason = catalog.trace.get("degraded_reason")
                if isinstance(reason, str) and reason:
                    degraded.append(f"retrieval_{reason}")
                limit = (
                    4 if turn.intent == AgentIntent.COMPARE else self._settings.agent_result_limit
                )
                candidate_products = [item.product for item in catalog.candidates[:limit]]
                candidate_ids = [item.id for item in candidate_products]
                if turn.intent == AgentIntent.COMPARE and len(candidate_ids) >= 2:
                    states.append("CompareProducts")
                    products = self._call_products_tool(
                        budget,
                        "compare_products",
                        candidate_ids,
                        self._tools.compare_products,
                        degraded,
                        fallback=candidate_products,
                    )
                elif turn.intent != AgentIntent.COMPARE:
                    states.append("GetProductDetail")
                    products = self._call_products_tool(
                        budget,
                        "get_product_detail",
                        candidate_ids,
                        self._tools.get_product_detail,
                        degraded,
                        fallback=candidate_products,
                    )
                else:
                    products = candidate_products

        if turn.intent == AgentIntent.COMPARE and len(products) < 2:
            states.append("NeedClarification")
            warnings.append("对比需要明确的 2-4 件商品。")
            return self._finalize_clarification(
                resolved_session_id,
                trace_id,
                turn,
                filters,
                soft_preferences,
                states,
                parser_mode,
                budget,
                model_calls,
                degraded,
                warnings,
                started,
                last_product_ids=[product.id for product in products],
                retrieval_trace=retrieval_trace,
                answer="请提供 2-4 件要比较的商品, 或补充更明确的型号。",
            )

        states.append("ComposeAnswer")
        evidence = build_evidence(products)
        plan_started = perf_counter()
        try:
            plan = self._model.plan_answer(
                message,
                [str(product.id) for product in products],
                evidence,
            )
            model_calls.append(
                ModelCallTrace(
                    phase="answer_plan",
                    model=self._model.identity,
                    status="ok",
                    latency_ms=_elapsed_ms(plan_started),
                )
            )
        except ProviderCircuitOpenError:
            degraded.append("answer_generation_circuit_open")
            plan = _safe_plan(products)
            model_calls.append(
                ModelCallTrace(
                    phase="answer_plan",
                    model=self._model.identity,
                    status="error",
                    latency_ms=_elapsed_ms(plan_started),
                )
            )
        except ProviderTimeoutError:
            degraded.append("answer_generation_timeout")
            plan = _safe_plan(products)
            model_calls.append(
                ModelCallTrace(
                    phase="answer_plan",
                    model=self._model.identity,
                    status="timeout",
                    latency_ms=_elapsed_ms(plan_started),
                )
            )
        except (ProviderError, ValueError):
            degraded.append("answer_generation_error")
            plan = _safe_plan(products)
            model_calls.append(
                ModelCallTrace(
                    phase="answer_plan",
                    model=self._model.identity,
                    status="error",
                    latency_ms=_elapsed_ms(plan_started),
                )
            )

        recommendations = build_recommendations(products, filters, evidence, plan)
        if turn.intent == AgentIntent.COMPARE and len(products) >= 2:
            comparison = build_comparison(products)
        states.append("ValidateCitations")
        valid, checked, citation_errors = validate_citations(recommendations, comparison, evidence)
        if not valid:
            states.append("SafeFallback")
            degraded.append("citation_validation_failed")
            recommendations = build_recommendations(
                products, filters, evidence, _safe_plan(products)
            )
            valid, checked, final_errors = validate_citations(recommendations, comparison, evidence)
            citation_errors = [*citation_errors, *final_errors]

        context_to_save = SessionContext(
            session_id=resolved_session_id,
            filters=filters,
            soft_preferences=soft_preferences,
            last_product_ids=[product.id for product in products[:4]],
            updated_at=datetime.now(UTC),
        )
        self._save_session(context_to_save, degraded, warnings)
        status = "degraded" if degraded else "completed"
        trace = AgentTrace(
            trace_id=trace_id,
            session_id=resolved_session_id,
            states=states,
            parser_mode=parser_mode,
            parsed_turn=turn,
            effective_filters=filters,
            tool_steps=budget.steps,
            model_calls=model_calls,
            citation_validation=CitationValidationTrace(
                valid=valid,
                checked_statement_count=checked,
                errors=citation_errors,
            ),
            retrieval=retrieval_trace,
            degraded_reasons=_dedupe(degraded),
            total_latency_ms=_elapsed_ms(started),
        )
        self._save_trace(trace, degraded, warnings)
        if trace.degraded_reasons != _dedupe(degraded):
            trace = trace.model_copy(update={"degraded_reasons": _dedupe(degraded)})
            status = "degraded"
        return AssistantResponse(
            status=status,
            session_id=resolved_session_id,
            answer=safe_answer_text(
                recommendations,
                comparison=comparison,
                degraded=bool(degraded),
            ),
            recommendations=recommendations,
            comparison=comparison,
            applied_filters=filters,
            soft_preferences=soft_preferences,
            relaxed_preferences=[],
            evidence=evidence,
            trace_id=trace_id,
            trace=trace,
            warnings=_dedupe(warnings),
        )

    def _call_products_tool(
        self,
        budget: _ToolBudget,
        name: str,
        product_ids: list[UUID],
        function: Callable[[list[UUID]], list[Product]],
        degraded: list[str],
        *,
        fallback: list[Product] | None = None,
    ) -> list[Product]:
        try:
            return budget.call(
                name,
                {"product_ids": [str(value) for value in product_ids]},
                lambda: function(product_ids),
                lambda value: {"product_count": len(value)},
            )
        except ToolStepLimitError:
            degraded.append("tool_step_limit")
            return fallback or []

    def _finalize_clarification(
        self,
        session_id: UUID,
        trace_id: UUID,
        turn: ParsedTurn,
        filters: SearchFiltersInput,
        soft_preferences: list[str],
        states: list[str],
        parser_mode: str,
        budget: _ToolBudget,
        model_calls: list[ModelCallTrace],
        degraded: list[str],
        warnings: list[str],
        started: float,
        *,
        last_product_ids: list[UUID] | None = None,
        retrieval_trace: dict[str, Any] | None = None,
        answer: str = "条件已更新。请告诉我接下来要找的耳机类型或使用场景。",
    ) -> AssistantResponse:
        self._save_session(
            SessionContext(
                session_id=session_id,
                filters=filters,
                soft_preferences=soft_preferences,
                last_product_ids=last_product_ids or [],
                updated_at=datetime.now(UTC),
            ),
            degraded,
            warnings,
        )
        trace = AgentTrace(
            trace_id=trace_id,
            session_id=session_id,
            states=states,
            parser_mode=parser_mode,
            parsed_turn=turn,
            effective_filters=filters,
            tool_steps=budget.steps,
            model_calls=model_calls,
            citation_validation=CitationValidationTrace(
                valid=True, checked_statement_count=0, errors=[]
            ),
            retrieval=retrieval_trace,
            degraded_reasons=_dedupe(degraded),
            total_latency_ms=_elapsed_ms(started),
        )
        self._save_trace(trace, degraded, warnings)
        if trace.degraded_reasons != _dedupe(degraded):
            trace = trace.model_copy(update={"degraded_reasons": _dedupe(degraded)})
        return AssistantResponse(
            status="needs_clarification",
            session_id=session_id,
            answer=answer,
            recommendations=[],
            comparison=None,
            applied_filters=filters,
            soft_preferences=soft_preferences,
            relaxed_preferences=[],
            evidence=[],
            trace_id=trace_id,
            trace=trace,
            warnings=_dedupe(warnings),
        )

    def _save_session(
        self,
        context: SessionContext,
        degraded: list[str],
        warnings: list[str],
    ) -> None:
        try:
            self._state.save_session(context)
        except StateStoreError:
            degraded.append("session_store_unavailable")
            warnings.append("本轮会话条件未能持久化。")

    def _save_trace(
        self,
        trace: AgentTrace,
        degraded: list[str],
        warnings: list[str],
    ) -> None:
        try:
            self._state.save_trace(trace)
        except StateStoreError:
            degraded.append("trace_store_unavailable")
            warnings.append("开发者轨迹未能持久化。")


def _product_filters(filters: SearchFiltersInput) -> ProductFilters:
    return ProductFilters(
        page=1,
        page_size=100,
        category=filters.category,
        brand=filters.brand,
        price_min=filters.price_min,
        price_max=filters.price_max,
        currency=filters.currency,
        wireless=filters.wireless,
        anc=filters.anc,
        battery_hours_min=filters.battery_hours_min,
        weight_grams_max=filters.weight_grams_max,
        color=filters.color,
        codec=filters.codec,
        water_resistance=filters.water_resistance,
    )


def _needs_clarification(
    turn: ParsedTurn,
    filters: SearchFiltersInput,
    preferences: list[str],
    asset_id: UUID | None,
) -> bool:
    if turn.intent == AgentIntent.COMPARE:
        return len(turn.referenced_product_ids) == 1
    return bool(
        turn.clear_all
        and not filters.model_dump(exclude_none=True)
        and not preferences
        and asset_id is None
    )


def _effective_query(message: str, preferences: list[str]) -> str:
    query = " ".join([message.strip(), *preferences]).strip()
    return (query or "耳机")[:300]


def _safe_plan(products: list[Product]) -> AnswerPlan:
    return AnswerPlan(
        recommendations=[
            PlannedRecommendation(
                product_id=product.id,
                evidence_ids=[f"fact:{product.id}:price_amount"],
            )
            for product in products
        ]
    )


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 3)
