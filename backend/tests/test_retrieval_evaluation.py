import pytest

from app.evaluation.retrieval_eval import (
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_reciprocal_rank,
)


def test_calculate_recall_at_k():
    gold_topics = ["lcd", "speech", "cost"]
    retrieved = [
        "We talked about the lcd display.",
        "The speech recognition feature was considered.",
        "General introduction remarks.",
    ]

    # At k=1: only 'lcd' found -> 1/3
    assert calculate_recall_at_k(retrieved, gold_topics, k=1) == pytest.approx(1 / 3)

    # At k=2: 'lcd' and 'speech' found -> 2/3
    assert calculate_recall_at_k(retrieved, gold_topics, k=2) == pytest.approx(2 / 3)

    # At k=3: 'lcd' and 'speech' found -> 2/3 (cost is missing)
    assert calculate_recall_at_k(retrieved, gold_topics, k=3) == pytest.approx(2 / 3)


def test_calculate_precision_at_k():
    gold_topics = ["titanium", "rubber"]
    retrieved = [
        "Titanium is very durable.",  # Relevant (has titanium)
        "Hello everyone let us begin.",  # Irrelevant
        "Rubber casing is cheap.",  # Relevant (has rubber)
        "Check the clock.",  # Irrelevant
    ]

    # At k=1: 1 relevant out of 1 -> 1.0
    assert calculate_precision_at_k(retrieved, gold_topics, k=1) == 1.0

    # At k=2: 1 relevant out of 2 -> 0.5
    assert calculate_precision_at_k(retrieved, gold_topics, k=2) == 0.5

    # At k=4: 2 relevant out of 4 -> 0.5
    assert calculate_precision_at_k(retrieved, gold_topics, k=4) == 0.5


def test_calculate_reciprocal_rank():
    gold_topics = ["battery"]

    # First item is relevant -> rank 1 -> 1.0
    assert calculate_reciprocal_rank(["Battery discussion"], gold_topics) == 1.0

    # Second item is relevant -> rank 2 -> 0.5
    assert calculate_reciprocal_rank(["Hello", "Battery options"], gold_topics) == 0.5

    # No items relevant -> 0.0
    assert calculate_reciprocal_rank(["Hello", "Goodbye"], gold_topics) == 0.0


def test_evaluation_empty_inputs():
    assert calculate_recall_at_k([], ["battery"], k=5) == 0.0
    assert calculate_precision_at_k([], ["battery"], k=5) == 0.0
    assert calculate_reciprocal_rank([], ["battery"]) == 0.0

