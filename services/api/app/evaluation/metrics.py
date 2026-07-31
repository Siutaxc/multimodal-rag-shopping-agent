"""Small, dependency-free information-retrieval metrics."""

import math


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Return the share of relevant identities found in the first k results."""

    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Return standard precision@k, using k as the denominator."""

    if k <= 0:
        raise ValueError("k must be positive")
    return sum(item in relevant for item in retrieved[:k]) / k


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    """Return reciprocal rank of the first relevant result, or zero."""

    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: list[str], relevance: dict[str, int], k: int) -> float:
    """Return nDCG@k with exponential gain for the checked-in grades."""

    actual = [relevance.get(item, 0) for item in retrieved[:k]]
    ideal = sorted(relevance.values(), reverse=True)[:k]
    ideal_dcg = _discounted_cumulative_gain(ideal)
    if ideal_dcg == 0:
        return 0.0
    return _discounted_cumulative_gain(actual) / ideal_dcg


def _discounted_cumulative_gain(grades: list[int]) -> float:
    return float(
        sum((2**grade - 1) / math.log2(rank + 1) for rank, grade in enumerate(grades, start=1))
    )
