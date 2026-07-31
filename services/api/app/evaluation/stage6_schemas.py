"""Dataset schema for bounded-agent, condition-mutation, and evidence evaluation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.agent.schemas import AgentIntent
from app.api.search import SearchFiltersInput


class Stage6AgentCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^agent-[0-9]{2}$")
    conversation_id: str = Field(pattern=r"^conversation-[a-z]$")
    message: str = Field(min_length=1, max_length=300)
    action: Literal["query", "compare_previous"] = "query"
    expected_intent: AgentIntent
    expected_filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)
    expected_status: Literal["completed", "needs_clarification", "degraded"] = "completed"
    expected_tools: list[str] = Field(min_length=1, max_length=4)
    minimum_recommendations: int = Field(default=1, ge=0, le=4)


class Stage6Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    fixture_source_version: str
    corpus_product_count: int = Field(gt=0)
    cases: list[Stage6AgentCase] = Field(min_length=10)

    @model_validator(mode="after")
    def validate_case_ids(self) -> "Stage6Dataset":
        ids = [item.id for item in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("stage-six case IDs must be unique")
        return self
