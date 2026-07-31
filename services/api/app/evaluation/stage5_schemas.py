"""Checked-in stage-five pure-image and image-plus-text relevance annotations."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.search import SearchFiltersInput


class Stage5EvaluationQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^(img|mix)-[0-9]{2}$")
    kind: Literal["pure_image", "multimodal"]
    reference_source_id: str = Field(min_length=1)
    query: str | None = Field(default=None, max_length=300)
    relevance: dict[str, int]
    filters: SearchFiltersInput = Field(default_factory=SearchFiltersInput)

    @model_validator(mode="after")
    def validate_kind_and_relevance(self) -> "Stage5EvaluationQuery":
        if self.kind == "pure_image" and self.query is not None:
            raise ValueError("pure image queries cannot contain text")
        if self.kind == "multimodal" and not (self.query or "").strip():
            raise ValueError("multimodal queries require text")
        if any(grade < 1 or grade > 3 for grade in self.relevance.values()):
            raise ValueError("relevance grades must be between 1 and 3")
        return self


class Stage5Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    fixture_source_version: str
    corpus_product_count: int = Field(gt=0)
    queries: list[Stage5EvaluationQuery] = Field(min_length=20)

    @model_validator(mode="after")
    def validate_query_groups(self) -> "Stage5Dataset":
        ids = [query.id for query in self.queries]
        if len(ids) != len(set(ids)):
            raise ValueError("stage-five query ids must be unique")
        if sum(query.kind == "pure_image" for query in self.queries) < 10:
            raise ValueError("stage five requires at least ten pure-image queries")
        if sum(query.kind == "multimodal" for query in self.queries) < 10:
            raise ValueError("stage five requires at least ten multimodal queries")
        return self
