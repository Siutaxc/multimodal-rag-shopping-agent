"""Validated stage-three evaluation dataset schemas."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.search import SearchFiltersInput


class EvaluationQuery(BaseModel):
    """One stable text query with graded source identities and optional hard filters."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^lex-[0-9]{2}$")
    query: str = Field(min_length=1, max_length=300)
    relevance: dict[str, int]
    filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)

    @model_validator(mode="after")
    def validate_relevance(self) -> "EvaluationQuery":
        if any(grade < 1 or grade > 3 for grade in self.relevance.values()):
            raise ValueError("relevance grades must be between 1 and 3")
        return self


class EvaluationDataset(BaseModel):
    """Exactly 30 versioned lexical queries required by the stage-three gate."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    fixture_source_version: str
    corpus_product_count: int = Field(gt=0)
    queries: list[EvaluationQuery]

    @model_validator(mode="after")
    def validate_query_set(self) -> "EvaluationDataset":
        if len(self.queries) != 30:
            raise ValueError("stage-three evaluation dataset must contain exactly 30 queries")
        query_ids = [query.id for query in self.queries]
        if len(query_ids) != len(set(query_ids)):
            raise ValueError("evaluation query ids must be unique")
        return self
