import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class FusedResult(Generic[T]):
    """Unified container representing a fused candidate item."""

    item: T
    item_id: uuid.UUID
    rrf_score: float
    keyword_rank: Optional[int] = None
    vector_rank: Optional[int] = None
    channel_scores: Dict[str, float] = field(default_factory=dict)


def reciprocal_rank_fusion(
    ranked_channels: Dict[str, List[T]],
    id_extractor: Callable[[T], uuid.UUID],
    weights: Optional[Dict[str, float]] = None,
    k: int = 60,
    score_extractors: Optional[Dict[str, Callable[[T], float]]] = None,
) -> List[FusedResult[T]]:
    """Compute Reciprocal Rank Fusion (RRF) across multiple ranked channels.

    Formula:
        RRF_Score(d) = sum_{m in channels} (w_m / (k + rank_m(d)))

    Args:
        ranked_channels: Dict mapping channel name (e.g. 'keyword', 'vector') to ordered list of items.
        id_extractor: Function returning unique UUID for each item.
        weights: Optional channel weights (defaults to 1.0 per channel).
        k: RRF smoothing constant (default 60).
        score_extractors: Optional mapping of channel name to function extracting raw channel score.

    Returns:
        List of FusedResult sorted descending by RRF score.
    """
    if not ranked_channels:
        return []

    channel_weights = weights or {}
    fused_map: Dict[uuid.UUID, FusedResult[T]] = {}

    for channel_name, items in ranked_channels.items():
        w_channel = channel_weights.get(channel_name, 1.0)
        # If weight is 0.0, this channel does not contribute to fusion score
        if w_channel <= 0.0:
            continue

        for rank_0, item in enumerate(items):
            item_id = id_extractor(item)
            rank_1 = rank_0 + 1
            rrf_contrib = w_channel / (k + rank_1)

            if item_id not in fused_map:
                fused_map[item_id] = FusedResult(
                    item=item,
                    item_id=item_id,
                    rrf_score=0.0,
                    channel_scores={},
                )

            res = fused_map[item_id]
            res.rrf_score += rrf_contrib

            if channel_name == "keyword":
                res.keyword_rank = rank_1
            elif channel_name == "vector":
                res.vector_rank = rank_1

            if score_extractors and channel_name in score_extractors:
                res.channel_scores[channel_name] = score_extractors[channel_name](item)

    # Sort candidates descending by RRF score
    sorted_results = sorted(fused_map.values(), key=lambda r: r.rrf_score, reverse=True)
    return sorted_results
