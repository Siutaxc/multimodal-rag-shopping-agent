"""Stage-eight expansion schemas kept separate from frozen earlier datasets."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.search import SearchFiltersInput


class Stage8EvaluationQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^s8-[0-9]{3}$")
    query: str = Field(min_length=1, max_length=300)
    relevance: dict[str, int]
    filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)
    cohort: str = Field(min_length=1, max_length=80)

    @model_validator(mode="after")
    def validate_relevance(self) -> "Stage8EvaluationQuery":
        if any(grade < 1 or grade > 3 for grade in self.relevance.values()):
            raise ValueError("relevance grades must be between 1 and 3")
        return self


class Stage8DatasetExtension(BaseModel):
    """Exactly 102 additions making 150 queries with the frozen stage 3/4 sets."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    frozen_lexical_dataset: str
    frozen_semantic_dataset: str
    fixture_source_version: str
    corpus_product_count: int = Field(gt=0)
    license: str
    queries: list[Stage8EvaluationQuery]

    @model_validator(mode="after")
    def validate_query_set(self) -> "Stage8DatasetExtension":
        if len(self.queries) != 102:
            raise ValueError("stage-eight extension must contain exactly 102 new queries")
        ids = [query.id for query in self.queries]
        if len(ids) != len(set(ids)):
            raise ValueError("stage-eight query ids must be unique")
        return self
