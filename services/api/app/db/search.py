"""PostgreSQL lexical retrieval with reviewed hard filters and stable ranking."""

from dataclasses import dataclass

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Product, ProductDocument, TextEmbedding
from app.db.products import ProductFilters, product_filter_clauses
from app.domain.products import DocumentType


@dataclass(frozen=True)
class SearchHit:
    """A product plus the inspectable score emitted by lexical retrieval."""

    product: Product
    lexical_score: float
    document_version: str


class LexicalSearchRepository:
    """Execute bound PostgreSQL FTS expressions; user input is never interpolated into SQL."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def search(self, query_text: str, filters: ProductFilters) -> tuple[list[SearchHit], int]:
        normalized_query = query_text.strip()
        tsquery = func.websearch_to_tsquery("simple", normalized_query)
        matches = ProductDocument.search_vector.op("@@")(tsquery)
        clauses = [
            ProductDocument.document_type == DocumentType.MAIN,
            matches,
            *product_filter_clauses(filters),
        ]
        base_rank = func.ts_rank_cd(ProductDocument.search_vector, tsquery, 32)
        score = (
            base_rank
            + case(
                (func.lower(Product.title).contains(normalized_query.casefold()), 1.0),
                else_=0.0,
            )
            + case(
                (func.lower(Product.brand) == normalized_query.casefold(), 0.75),
                else_=0.0,
            )
        ).label("lexical_score")

        total = self._session.scalar(
            select(func.count(Product.id))
            .join(ProductDocument, ProductDocument.product_id == Product.id)
            .where(*clauses)
        )
        statement = (
            select(Product, score, ProductDocument.document_version)
            .join(ProductDocument, ProductDocument.product_id == Product.id)
            .where(*clauses)
            .order_by(score.desc(), Product.title.asc(), Product.id.asc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        rows = self._session.execute(statement).all()
        hits = [
            SearchHit(
                product=row[0],
                lexical_score=float(row[1] or 0.0),
                document_version=row[2],
            )
            for row in rows
        ]
        return hits, int(total or 0)


@dataclass(frozen=True)
class DenseSearchHit:
    """A product plus cosine similarity from one exact vector version."""

    product: Product
    dense_score: float
    document_version: str


class DenseSearchRepository:
    """Execute pgvector cosine search without crossing vector-version boundaries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def search(
        self,
        query_vector: list[float],
        filters: ProductFilters,
        *,
        model_name: str,
        model_version: str,
        dimension: int,
        document_version: str,
        limit: int,
    ) -> tuple[list[DenseSearchHit], int]:
        distance = TextEmbedding.embedding.cosine_distance(query_vector).label("distance")
        clauses = [
            ProductDocument.document_type == DocumentType.MAIN,
            TextEmbedding.model_name == model_name,
            TextEmbedding.model_version == model_version,
            TextEmbedding.dimension == dimension,
            TextEmbedding.document_version == document_version,
            TextEmbedding.status == "ready",
            TextEmbedding.embedding.is_not(None),
            *product_filter_clauses(filters),
        ]
        joined = (
            select(Product.id)
            .join(ProductDocument, ProductDocument.product_id == Product.id)
            .join(TextEmbedding, TextEmbedding.document_id == ProductDocument.id)
            .where(*clauses)
        )
        total = self._session.scalar(select(func.count()).select_from(joined.subquery()))
        statement = (
            select(Product, distance)
            .join(ProductDocument, ProductDocument.product_id == Product.id)
            .join(TextEmbedding, TextEmbedding.document_id == ProductDocument.id)
            .where(*clauses)
            .options(selectinload(Product.review_evidence))
            .order_by(distance.asc(), Product.title.asc(), Product.id.asc())
            .limit(limit)
        )
        rows = self._session.execute(statement).all()
        return (
            [
                DenseSearchHit(
                    product=row[0],
                    dense_score=max(-1.0, min(1.0, 1.0 - float(row[1]))),
                    document_version=document_version,
                )
                for row in rows
            ],
            int(total or 0),
        )
