import json
import math
import re
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.models.memory import (
    Memory,
    MemoryStatus,
    MemoryType,
)
from app.schemas.memory import MemoryRelationshipResponse
from app.schemas.retrieval import (
    EvidencePackResponse,
    MemoryEvidenceItem,
    RetrievalFilter,
    RetrievalMethod,
    RetrievalRequest,
    TranscriptEvidenceItem,
)
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.query_processor import QueryProcessor, get_query_processor
from app.services.rank_fusion import FusedResult, reciprocal_rank_fusion

logger = get_logger("app.services.hybrid_retrieval")


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class HybridRetrievalService:
    """Service orchestrating lexical, dense vector, and temporal memory retrieval with RRF ranking."""

    def __init__(
        self,
        db: Session,
        embedding_service: Optional[EmbeddingService] = None,
        query_processor: Optional[QueryProcessor] = None,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service or get_embedding_service()
        self.query_processor = query_processor or get_query_processor()
        self.is_postgres = bool(self.db.bind and self.db.bind.dialect.name == "postgresql")

    def search_turns_keyword(
        self,
        keyword_query: str,
        filters: RetrievalFilter,
        limit: int = 20,
    ) -> List[Tuple[TranscriptTurn, float]]:
        """Perform lexical keyword search over TranscriptTurns."""
        if not keyword_query or not keyword_query.strip():
            return []

        base_query = (
            select(TranscriptTurn)
            .join(Meeting, TranscriptTurn.meeting_id == Meeting.id)
            .join(Team, Meeting.team_id == Team.id)
            .outerjoin(Speaker, TranscriptTurn.speaker_id == Speaker.id)
            .options(
                selectinload(TranscriptTurn.speaker),
                selectinload(TranscriptTurn.meeting),
            )
        )

        conditions = []
        if filters.team_code:
            conditions.append(Team.team_code == filters.team_code.upper())
        if filters.meeting_code:
            conditions.append(Meeting.meeting_code == filters.meeting_code.lower())
        if filters.speaker_label:
            conditions.append(Speaker.speaker_label.ilike(f"%{filters.speaker_label}%"))
        if filters.sequence_letters:
            lowers = [s.lower() for s in filters.sequence_letters]
            conditions.append(Meeting.sequence_letter.in_(lowers))

        if self.is_postgres:
            # Native PostgreSQL Full-Text Search
            ts_query = func.websearch_to_tsquery("english", keyword_query)
            query = (
                base_query.where(
                    TranscriptTurn.search_vector.op("@@")(ts_query),
                    *conditions,
                )
                .order_by(desc(func.ts_rank_cd(TranscriptTurn.search_vector, ts_query)))
                .limit(limit)
            )
            results = self.db.execute(query).scalars().all()
            return [(t, 1.0 / (idx + 1)) for idx, t in enumerate(results)]

        else:
            # SQLite / Test Fallback: Token-based lexical matching
            tokens = [t.lower() for t in re.findall(r"\b[A-Za-z0-9\-\_]{2,}\b", keyword_query)]
            if conditions:
                base_query = base_query.where(*conditions)

            all_candidates = self.db.execute(base_query).scalars().all()
            scored_candidates: List[Tuple[TranscriptTurn, float]] = []

            for turn in all_candidates:
                text_lower = (turn.raw_text or "").lower()
                matches = sum(1 for tok in tokens if tok in text_lower)
                if matches > 0:
                    # Score based on token coverage
                    score = matches / max(1, len(tokens))
                    scored_candidates.append((turn, score))

            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            return scored_candidates[:limit]

    def search_turns_vector(
        self,
        query_text: str,
        filters: RetrievalFilter,
        limit: int = 20,
    ) -> List[Tuple[TranscriptTurn, float]]:
        """Perform dense vector semantic search over TranscriptTurns."""
        if not query_text or not query_text.strip():
            return []

        try:
            embeddings = self.embedding_service.generate_embeddings([query_text])
            query_vector = embeddings[0] if embeddings else None
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return []

        if not query_vector:
            return []

        base_query = (
            select(TranscriptTurn)
            .join(Meeting, TranscriptTurn.meeting_id == Meeting.id)
            .join(Team, Meeting.team_id == Team.id)
            .outerjoin(Speaker, TranscriptTurn.speaker_id == Speaker.id)
            .where(TranscriptTurn.embedding.isnot(None))
            .options(
                selectinload(TranscriptTurn.speaker),
                selectinload(TranscriptTurn.meeting),
            )
        )

        conditions = []
        if filters.team_code:
            conditions.append(Team.team_code == filters.team_code.upper())
        if filters.meeting_code:
            conditions.append(Meeting.meeting_code == filters.meeting_code.lower())
        if filters.speaker_label:
            conditions.append(Speaker.speaker_label.ilike(f"%{filters.speaker_label}%"))
        if filters.sequence_letters:
            lowers = [s.lower() for s in filters.sequence_letters]
            conditions.append(Meeting.sequence_letter.in_(lowers))

        if self.is_postgres:
            # Native pgvector cosine distance
            query = (
                base_query.where(*conditions)
                .order_by(TranscriptTurn.embedding.cosine_distance(query_vector).asc())
                .limit(limit)
            )
            turns = self.db.execute(query).scalars().all()
            return [(t, 1.0 / (idx + 1)) for idx, t in enumerate(turns)]

        else:
            # SQLite / Test Fallback: Compute in-memory cosine similarity
            if conditions:
                base_query = base_query.where(*conditions)

            turns = self.db.execute(base_query).scalars().all()
            scored: List[Tuple[TranscriptTurn, float]] = []

            for turn in turns:
                raw_emb = turn.embedding
                if isinstance(raw_emb, str):
                    try:
                        raw_emb = json.loads(raw_emb)
                    except Exception:
                        continue
                if isinstance(raw_emb, list):
                    sim = cosine_similarity(query_vector, raw_emb)
                    scored.append((turn, sim))

            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:limit]

    def search_temporal_memories(
        self,
        query_text: str,
        filters: RetrievalFilter,
        limit: int = 15,
    ) -> Tuple[List[Memory], List[Memory]]:
        """Retrieve relevant temporal memories, separating supported decisions/actions from unresolved disagreements."""
        base_query = (
            select(Memory)
            .join(Meeting, Memory.meeting_id == Meeting.id)
            .join(Team, Memory.team_id == Team.id)
            .options(
                selectinload(Memory.outgoing_relationships),
                selectinload(Memory.incoming_relationships),
                selectinload(Memory.meeting),
                selectinload(Memory.team),
            )
        )

        conditions = []
        if filters.team_code:
            conditions.append(Team.team_code == filters.team_code.upper())
        if filters.meeting_code:
            conditions.append(Meeting.meeting_code == filters.meeting_code.lower())
        if filters.memory_type:
            conditions.append(Memory.memory_type == filters.memory_type.upper())
        if filters.status:
            conditions.append(Memory.status == filters.status.lower())

        # Substring / Topic match if query provided
        if query_text and query_text.strip():
            tokens = [t.lower() for t in re.findall(r"\b[A-Za-z0-9\-\_]{2,}\b", query_text)]
            if tokens:
                match_conds = [
                    or_(
                        Memory.statement.ilike(f"%{tok}%"),
                        Memory.quote.ilike(f"%{tok}%"),
                    )
                    for tok in tokens[:5]
                ]
                conditions.append(or_(*match_conds))

        if conditions:
            base_query = base_query.where(*conditions)

        all_memories = list(
            self.db.execute(
                base_query.order_by(Memory.meeting_order.asc(), Memory.created_at.asc())
            )
            .scalars()
            .all()
        )

        # Graph Traversal: Pull in any directly linked superseding or superseded memories
        linked_memory_ids = set()
        for mem in all_memories:
            for rel in mem.outgoing_relationships:
                linked_memory_ids.add(rel.target_memory_id)
            for rel in mem.incoming_relationships:
                linked_memory_ids.add(rel.source_memory_id)

        existing_ids = {m.id for m in all_memories}
        missing_ids = [mid for mid in linked_memory_ids if mid not in existing_ids]

        if missing_ids:
            linked_mems = (
                self.db.execute(
                    select(Memory)
                    .where(Memory.id.in_(missing_ids))
                    .options(
                        selectinload(Memory.outgoing_relationships),
                        selectinload(Memory.incoming_relationships),
                        selectinload(Memory.meeting),
                        selectinload(Memory.team),
                    )
                )
                .scalars()
                .all()
            )
            all_memories.extend(linked_mems)

        regular_memories: List[Memory] = []
        unresolved_disagreements: List[Memory] = []

        for mem in all_memories:
            if (
                mem.memory_type == MemoryType.DISAGREEMENT.value
                and mem.status == MemoryStatus.OPEN.value
            ):
                unresolved_disagreements.append(mem)
            else:
                regular_memories.append(mem)

        # Prioritize supported current decisions, but keep superseded decisions for temporal history
        regular_memories.sort(
            key=lambda m: (
                0 if m.status == MemoryStatus.CURRENT.value else 1,
                m.meeting_order,
            )
        )

        return regular_memories[:limit], unresolved_disagreements[:limit]

    def execute_retrieval(self, request: RetrievalRequest) -> EvidencePackResponse:
        """Execute unified hybrid retrieval with reciprocal rank fusion and evidence pack generation."""
        # 1. Process query and extract entities/filters
        processed = self.query_processor.process_query(request.query)

        # Merge explicit request filters with extracted filters
        team_code = request.team_code or processed.extracted_team
        meeting_code = request.meeting_code or (
            processed.extracted_meetings[0] if processed.extracted_meetings else None
        )

        filters = RetrievalFilter(
            team_code=team_code,
            meeting_code=meeting_code,
            speaker_label=processed.extracted_speakers[0] if processed.extracted_speakers else None,
        )

        search_kw = processed.cleaned_keyword_query or request.query

        # 2. Execute retrieval channels based on requested method
        ranked_channels: Dict[str, List[TranscriptTurn]] = {}
        score_maps: Dict[str, Callable[[TranscriptTurn], float]] = {}

        if request.method in [RetrievalMethod.HYBRID.value, RetrievalMethod.KEYWORD.value]:
            kw_results = self.search_turns_keyword(
                keyword_query=search_kw,
                filters=filters,
                limit=request.limit * 2,
            )
            ranked_channels["keyword"] = [t for t, _ in kw_results]
            kw_score_dict = {t.id: s for t, s in kw_results}
            score_maps["keyword"] = lambda t: kw_score_dict.get(t.id, 0.0)

        if request.method in [RetrievalMethod.HYBRID.value, RetrievalMethod.VECTOR.value]:
            vec_results = self.search_turns_vector(
                query_text=request.query,
                filters=filters,
                limit=request.limit * 2,
            )
            ranked_channels["vector"] = [t for t, _ in vec_results]
            vec_score_dict = {t.id: s for t, s in vec_results}
            score_maps["vector"] = lambda t: vec_score_dict.get(t.id, 0.0)

        # 3. Fuse channels using Reciprocal Rank Fusion (RRF)
        weights = {
            "keyword": request.weight_keyword,
            "vector": request.weight_vector,
        }

        # Handle single channel weight adjustments if requested method is strictly keyword or vector
        if request.method == RetrievalMethod.KEYWORD.value:
            weights["keyword"] = 1.0
            weights["vector"] = 0.0
        elif request.method == RetrievalMethod.VECTOR.value:
            weights["keyword"] = 0.0
            weights["vector"] = 1.0

        fused: List[FusedResult[TranscriptTurn]] = reciprocal_rank_fusion(
            ranked_channels=ranked_channels,
            id_extractor=lambda t: t.id,
            weights=weights,
            k=request.rrf_k,
            score_extractors=score_maps,
        )

        top_fused = fused[: request.limit]

        # 4. Convert to TranscriptEvidenceItems
        evidence_items: List[TranscriptEvidenceItem] = []
        cross_meeting_summary: Dict[str, int] = {}

        for fr in top_fused:
            turn = fr.item
            mtg = turn.meeting
            mtg_code = mtg.meeting_code if mtg else "unknown"
            cross_meeting_summary[mtg_code] = cross_meeting_summary.get(mtg_code, 0) + 1

            evidence_items.append(
                TranscriptEvidenceItem(
                    turn_id=turn.id,
                    meeting_id=turn.meeting_id,
                    meeting_code=mtg_code,
                    meeting_number=mtg.meeting_number if mtg else None,
                    sequence_letter=mtg.sequence_letter if mtg else None,
                    turn_index=turn.turn_index,
                    speaker_label=turn.speaker.speaker_label if turn.speaker else "Unknown",
                    speaker_role=turn.speaker.role if turn.speaker else None,
                    start_time_str=turn.start_time_str,
                    raw_text=turn.raw_text,
                    score=round(fr.rrf_score, 5),
                    retrieval_method=request.method,
                    keyword_rank=fr.keyword_rank,
                    vector_rank=fr.vector_rank,
                )
            )

        # 5. Retrieve related temporal memories if requested
        memory_items: List[MemoryEvidenceItem] = []
        disagreement_items: List[MemoryEvidenceItem] = []

        if request.include_temporal_memories:
            regular_mems, open_disagreements = self.search_temporal_memories(
                query_text=search_kw,
                filters=filters,
                limit=10,
            )

            for m in regular_mems:
                memory_items.append(
                    MemoryEvidenceItem(
                        memory_id=m.id,
                        team_code=m.team.team_code if m.team else "unknown",
                        meeting_code=m.meeting.meeting_code if m.meeting else "unknown",
                        sequence_letter=m.sequence_letter,
                        meeting_order=m.meeting_order,
                        memory_type=m.memory_type,
                        status=m.status,
                        statement=m.statement,
                        quote=m.quote,
                        speaker_label=m.speaker_label,
                        speaker_role=m.speaker_role,
                        turn_id=m.turn_id,
                        confidence=m.confidence,
                        metadata_json=m.metadata_json or {},
                        outgoing_relationships=[
                            MemoryRelationshipResponse.model_validate(rel)
                            for rel in m.outgoing_relationships
                        ],
                        incoming_relationships=[
                            MemoryRelationshipResponse.model_validate(rel)
                            for rel in m.incoming_relationships
                        ],
                    )
                )

            for d in open_disagreements:
                disagreement_items.append(
                    MemoryEvidenceItem(
                        memory_id=d.id,
                        team_code=d.team.team_code if d.team else "unknown",
                        meeting_code=d.meeting.meeting_code if d.meeting else "unknown",
                        sequence_letter=d.sequence_letter,
                        meeting_order=d.meeting_order,
                        memory_type=d.memory_type,
                        status=d.status,
                        statement=d.statement,
                        quote=d.quote,
                        speaker_label=d.speaker_label,
                        speaker_role=d.speaker_role,
                        turn_id=d.turn_id,
                        confidence=d.confidence,
                        metadata_json=d.metadata_json or {},
                        outgoing_relationships=[
                            MemoryRelationshipResponse.model_validate(rel)
                            for rel in d.outgoing_relationships
                        ],
                        incoming_relationships=[
                            MemoryRelationshipResponse.model_validate(rel)
                            for rel in d.incoming_relationships
                        ],
                    )
                )

        return EvidencePackResponse(
            query=request.query,
            processed_query=processed,
            retrieval_method=request.method,
            total_results=len(evidence_items),
            transcript_segments=evidence_items,
            temporal_memories=memory_items,
            unresolved_disagreements=disagreement_items,
            cross_meeting_summary=cross_meeting_summary,
        )
