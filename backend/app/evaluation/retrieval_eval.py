import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.schemas.retrieval import RetrievalRequest
from app.services.hybrid_retrieval_service import HybridRetrievalService

logger = get_logger("app.evaluation.retrieval")


@dataclass
class BenchmarkItem:
    """A benchmark query with ground-truth team, verified topics, and target meetings."""

    question_id: str
    team: str
    query: str
    gold_topics: List[str]
    expected_meetings: List[str]
    is_manually_verified: bool = True


# Controlled benchmark dataset curated from data/raw/questions.json
BENCHMARK_ITEMS: List[BenchmarkItem] = [
    BenchmarkItem(
        question_id="Q01",
        team="TS3006",
        query="Team TS3006 planned both an LCD screen and speech recognition. When the costs forced a cut, which of the two did they drop, which did they keep, and what reason was given for keeping it?",
        gold_topics=["lcd", "speech recognition", "cost", "cut"],
        expected_meetings=["ts3006a", "ts3006b", "ts3006c", "ts3006d"],
    ),
    BenchmarkItem(
        question_id="Q02",
        team="ES2003",
        query="Team ES2003 leaned towards one material for the case and then switched to another. What did they lean towards first, what did they end with, and why did they switch?",
        gold_topics=["material", "titanium", "rubber", "plastic", "switch"],
        expected_meetings=["es2003a", "es2003b", "es2003c"],
    ),
    BenchmarkItem(
        question_id="Q03",
        team="TS3009",
        query="Team TS3009 planned a titanium back for their remote. Who first proposed replacing the titanium, what did they propose instead, and was the titanium kept in the end?",
        gold_topics=["titanium", "replace", "rubber", "plastic"],
        expected_meetings=["ts3009a", "ts3009b", "ts3009c", "ts3009d"],
    ),
    BenchmarkItem(
        question_id="Q04",
        team="TS3011",
        query="Team TS3011 chose a combined energy source for their remote. What was the combination, and what happened to it when the costs were added up?",
        gold_topics=["energy", "solar", "kinetic", "battery", "cost"],
        expected_meetings=["ts3011a", "ts3011b", "ts3011c", "ts3011d"],
    ),
    BenchmarkItem(
        question_id="Q05",
        team="TS3007",
        query="Team TS3007's energy source changed between meetings. What did they first settle on, what did they end with, and who proposed the change?",
        gold_topics=["energy", "solar", "kinetic", "battery", "change"],
        expected_meetings=["ts3007a", "ts3007b", "ts3007c", "ts3007d"],
    ),
    BenchmarkItem(
        question_id="Q06",
        team="ES2008",
        query="Team ES2008 wanted a feature to stop the remote getting lost. What happened to that feature, who raised the main objection to it, and what was the objection?",
        gold_topics=["lost", "find", "locater", "locator", "objection"],
        expected_meetings=["es2008a", "es2008b", "es2008c"],
    ),
    BenchmarkItem(
        question_id="Q12",
        team="ES2004",
        query="Team ES2004 considered voice recognition as a way to find the remote when it is lost. What happened to it in the final design, why, and what did they say would still make the remote easy to find?",
        gold_topics=["voice recognition", "lost", "find", "easy"],
        expected_meetings=["es2004a", "es2004b", "es2004c", "es2004d"],
    ),
    BenchmarkItem(
        question_id="Q13",
        team="TS3004",
        query="Team TS3004 changed its mind about speech recognition more than once. Was speech recognition in their final design, and in which of their four meetings did they last reverse their position on it?",
        gold_topics=["speech recognition", "reverse", "design"],
        expected_meetings=["ts3004a", "ts3004b", "ts3004c", "ts3004d"],
    ),
    BenchmarkItem(
        question_id="Q22",
        team="ES2010",
        query="Team ES2010 discussed several battery options. Who suggested a lithium battery, what did another member prefer instead and why, and what was the final choice?",
        gold_topics=["battery", "lithium", "regular", "prefer"],
        expected_meetings=["es2010a", "es2010b", "es2010c", "es2010d"],
    ),
    BenchmarkItem(
        question_id="Q24",
        team="ES2002",
        query="What power source did Team ES2002 first agree on, what addition did their project manager like the idea of, and what did the final design use?",
        gold_topics=["power", "solar", "kinetic", "battery", "project manager"],
        expected_meetings=["es2002a", "es2002b", "es2002c", "es2002d"],
    ),
]


def calculate_recall_at_k(
    retrieved_texts: List[str],
    gold_topics: List[str],
    k: int,
) -> float:
    """Fraction of gold topics present in the top-k retrieved texts."""
    if not gold_topics:
        return 1.0
    top_k_text = " ".join(retrieved_texts[:k]).lower()
    found = sum(1 for topic in gold_topics if topic.lower() in top_k_text)
    return found / len(gold_topics)


def calculate_precision_at_k(
    retrieved_texts: List[str],
    gold_topics: List[str],
    k: int,
) -> float:
    """Fraction of the top-k retrieved items that contain at least one gold topic."""
    if k <= 0 or not retrieved_texts:
        return 0.0
    eval_slice = retrieved_texts[:k]
    relevant_count = 0
    for text in eval_slice:
        t_low = text.lower()
        if any(topic.lower() in t_low for topic in gold_topics):
            relevant_count += 1
    return relevant_count / len(eval_slice)


def calculate_reciprocal_rank(
    retrieved_texts: List[str],
    gold_topics: List[str],
) -> float:
    """1 / rank of the first retrieved item containing any gold topic (0.0 if not found)."""
    for rank_0, text in enumerate(retrieved_texts):
        t_low = text.lower()
        if any(topic.lower() in t_low for topic in gold_topics):
            return 1.0 / (rank_0 + 1)
    return 0.0


@dataclass
class ChannelEvaluationMetrics:
    """Aggregated evaluation metrics for a specific retrieval method."""

    method: str
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    precision_at_5: float = 0.0
    precision_at_10: float = 0.0
    mrr: float = 0.0
    avg_latency_ms: float = 0.0
    multi_meeting_rate: float = 0.0
    evaluated_queries: int = 0


class RetrievalEvaluator:
    """Benchmark harness comparing keyword, vector, and hybrid RRF retrieval."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.retrieval_service = HybridRetrievalService(db=db)

    def evaluate_method(
        self,
        method: str,
        items: Optional[List[BenchmarkItem]] = None,
        limit: int = 10,
    ) -> ChannelEvaluationMetrics:
        """Run benchmark evaluation for a given method across benchmark items."""
        eval_items = items or BENCHMARK_ITEMS
        metrics = ChannelEvaluationMetrics(method=method, evaluated_queries=len(eval_items))

        total_r5 = 0.0
        total_r10 = 0.0
        total_p5 = 0.0
        total_p10 = 0.0
        total_rr = 0.0
        total_latency = 0.0
        multi_meeting_successes = 0

        for b_item in eval_items:
            req = RetrievalRequest(
                query=b_item.query,
                team_code=b_item.team,
                method=method,
                limit=limit,
            )

            start = time.perf_counter()
            pack = self.retrieval_service.execute_retrieval(req)
            elapsed_ms = (time.perf_counter() - start) * 1000.0

            total_latency += elapsed_ms

            retrieved_texts = [turn.raw_text for turn in pack.transcript_segments]

            total_r5 += calculate_recall_at_k(retrieved_texts, b_item.gold_topics, k=5)
            total_r10 += calculate_recall_at_k(retrieved_texts, b_item.gold_topics, k=10)
            total_p5 += calculate_precision_at_k(retrieved_texts, b_item.gold_topics, k=5)
            total_p10 += calculate_precision_at_k(retrieved_texts, b_item.gold_topics, k=10)
            total_rr += calculate_reciprocal_rank(retrieved_texts, b_item.gold_topics)

            # Check multi-meeting evidence coverage: distinct meetings >= 2
            distinct_meetings = {turn.meeting_code for turn in pack.transcript_segments}
            if len(distinct_meetings) >= 2:
                multi_meeting_successes += 1

        n = max(1, len(eval_items))
        metrics.recall_at_5 = round(total_r5 / n, 4)
        metrics.recall_at_10 = round(total_r10 / n, 4)
        metrics.precision_at_5 = round(total_p5 / n, 4)
        metrics.precision_at_10 = round(total_p10 / n, 4)
        metrics.mrr = round(total_rr / n, 4)
        metrics.avg_latency_ms = round(total_latency / n, 2)
        metrics.multi_meeting_rate = round(multi_meeting_successes / n, 4)

        return metrics

    def run_comparative_benchmark(
        self,
        items: Optional[List[BenchmarkItem]] = None,
    ) -> Dict[str, ChannelEvaluationMetrics]:
        """Run keyword, vector, and hybrid evaluations side by side."""
        methods = ["keyword", "vector", "hybrid"]
        results = {}
        for m in methods:
            results[m] = self.evaluate_method(method=m, items=items)
        return results
