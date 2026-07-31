"""Schemas for stage-four semantic additions without editing the frozen stage-three set."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.search import SearchFiltersInput


class SemanticEvaluationQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^sem-[0-9]{2}$")
    query: str = Field(min_length=1, max_length=300)
    relevance: dict[str, int]
    filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)

    @model_validator(mode="after")
    def validate_relevance(self) -> "SemanticEvaluationQuery":
        if any(grade < 1 or grade > 3 for grade in self.relevance.values()):
            raise ValueError("relevance grades must be between 1 and 3")
        return self


class Stage4DatasetExtension(BaseModel):
    """New scenario queries evaluated together with an immutable base dataset."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    base_dataset: str
    fixture_source_version: str
    corpus_product_count: int = Field(gt=0)
    semantic_queries: list[SemanticEvaluationQuery] = Field(min_length=10)

    @model_validator(mode="after")
    def validate_query_ids(self) -> "Stage4DatasetExtension":
        ids = [query.id for query in self.semantic_queries]
        if len(ids) != len(set(ids)):
            raise ValueError("semantic evaluation query ids must be unique")
        return self
