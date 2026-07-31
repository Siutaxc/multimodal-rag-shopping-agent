"""HTTP endpoints for the bounded agent, comparisons, sessions, and development traces."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.agent.schemas import AssistantResponse, FilterField, SessionContext
from app.agent.service import BoundedShoppingAgent
from app.agent.state import AgentStateStore, StateStoreError, create_agent_state_store
from app.agent.tools import ShoppingAgentTools
from app.api.multimodal import get_multimodal_search_service
from app.api.products import get_product_repository
from app.api.search import SearchFiltersInput, get_search_service
from app.core.settings import Settings, get_settings
from app.db.products import ProductRepository
from app.images.search import AssetNotFoundError, MultimodalSearchService
from app.providers.agent import create_agent_model_provider
from app.retrieval.hybrid import HybridSearchService

router = APIRouter(tags=["assistant"])


class AssistantQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=300)
    session_id: UUID | None = None
    asset_id: UUID | None = None
    filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)
    clear_fields: list[FilterField] = Field(default_factory=list, max_length=len(FilterField))
    product_ids: list[UUID] = Field(default_factory=list, max_length=4)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message must contain text")
        return normalized

    @model_validator(mode="after")
    def unique_ids_and_clear_fields(self) -> "AssistantQueryRequest":
        if len(self.product_ids) != len(set(self.product_ids)):
            raise ValueError("product_ids must be unique")
        if len(self.clear_fields) != len(set(self.clear_fields)):
            raise ValueError("clear_fields must be unique")
        return self


class CompareProductsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_ids: list[UUID] = Field(min_length=2, max_length=4)
    session_id: UUID | None = None

    @model_validator(mode="after")
    def unique_product_ids(self) -> "CompareProductsRequest":
        if len(self.product_ids) != len(set(self.product_ids)):
            raise ValueError("product_ids must be unique")
        return self


def get_agent_state_store(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AgentStateStore:
    return create_agent_state_store(settings)


def get_bounded_agent(
    products: Annotated[ProductRepository, Depends(get_product_repository)],
    text_search: Annotated[HybridSearchService, Depends(get_search_service)],
    multimodal_search: Annotated[MultimodalSearchService, Depends(get_multimodal_search_service)],
    state_store: Annotated[AgentStateStore, Depends(get_agent_state_store)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> BoundedShoppingAgent:
    tools = ShoppingAgentTools(products, text_search, multimodal_search)
    return BoundedShoppingAgent(
        tools,
        state_store,
        create_agent_model_provider(settings),
        settings,
    )


@router.post("/assistant/query", response_model=AssistantResponse)
def assistant_query(
    request: AssistantQueryRequest,
    agent: Annotated[BoundedShoppingAgent, Depends(get_bounded_agent)],
) -> AssistantResponse:
    try:
        return agent.query(
            request.message,
            session_id=request.session_id,
            asset_id=request.asset_id,
            explicit_filters=request.filters,
            clear_fields=request.clear_fields,
            product_ids=request.product_ids,
        )
    except AssetNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="asset not found"
        ) from error


@router.post("/products/compare", response_model=AssistantResponse)
def compare_products(
    request: CompareProductsRequest,
    agent: Annotated[BoundedShoppingAgent, Depends(get_bounded_agent)],
) -> AssistantResponse:
    return agent.query(
        "比较指定的商品",
        session_id=request.session_id,
        product_ids=request.product_ids,
    )


@router.get("/sessions/{session_id}", response_model=SessionContext)
def get_session_context(
    session_id: UUID,
    state_store: Annotated[AgentStateStore, Depends(get_agent_state_store)],
) -> SessionContext:
    try:
        context = state_store.get_session(session_id)
    except StateStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="session store unavailable",
        ) from error
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    return context


@router.get("/traces/{trace_id}")
def get_agent_trace(
    trace_id: UUID,
    state_store: Annotated[AgentStateStore, Depends(get_agent_state_store)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> object:
    if settings.app_env == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="trace not found")
    try:
        trace = state_store.get_trace(trace_id)
    except StateStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="trace store unavailable",
        ) from error
    if trace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="trace not found")
    return trace
