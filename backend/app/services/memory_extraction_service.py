import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.dataset import Meeting, Team, TranscriptTurn
from app.models.memory import (
    Memory,
    MemoryExtractionRun,
    MemoryStatus,
    MemoryType,
)
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.services.evidence_validator import EvidenceValidator, get_evidence_validator
from app.services.llm_client import BaseLLMClient, get_llm_client
from app.services.temporal_reasoning import TemporalReasoningService

logger = get_logger("app.services.memory_extraction")


class MemoryExtractionError(AppException):
    """Raised when memory extraction process encounters an unrecoverable error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=500, details=details or {})


EXTRACTION_SYSTEM_PROMPT = """You are a senior meeting intelligence extraction system.
Your job is to analyze transcript turns from team design meetings and extract atomic memory records.

EXTRACT ONLY THESE TYPES:
- DECISION: Concrete design, architectural, technical, marketing, or project decisions, including changes to previous decisions.
- ACTION: Explicit task commitments, assignments, next steps, and their assigned owners.
- PREFERENCE: Explicit customer, user, or stakeholder preferences and aesthetic choices.
- REQUIREMENT: Explicit functional, electrical, mechanical, financial, or user requirements.
- DISAGREEMENT: Active disagreements, opposing views, arguments, or unresolved conflicts.
- ENTITY: Core project components, materials, or target market definitions.

CRITICAL EVIDENCE & CITATION RULES:
1. The 'quote' field MUST be an EXACT, VERBATIM substring copied directly from the turn text.
2. The quote MUST contain at least 6 consecutive words from the speaker's utterance.
3. NEVER paraphrase, alter, or construct quotes. Fabricated quotes will be strictly rejected.
4. 'turn_index' MUST be the exact numeric index of the turn where the quote was spoken.
5. 'speaker_label' MUST be the exact speaker label of that turn (e.g. 'Speaker A').
6. For ACTION items: do NOT invent an owner unless explicitly stated or addressed in the utterance.
7. 'topic': A short canonical snake_case string identifying the concept (e.g. 'battery_type', 'case_material', 'remote_shape', 'target_budget').

JSON SCHEMA:
{
  "memories": [
    {
      "memory_type": "DECISION",
      "statement": "The team decided to use kinetic power instead of standard batteries.",
      "quote": "we are definitely going with kinetic power for this remote",
      "speaker_label": "Speaker B",
      "turn_index": 12,
      "confidence": 0.95,
      "metadata": {
        "topic": "power_source",
        "owner": null
      },
      "relationship_type": null,
      "relationship_rationale": null,
      "is_ambiguous": false
    }
  ]
}
"""


class MemoryExtractionService:
    """Service orchestrating LLM memory extraction, verbatim evidence validation, and temporal linking."""

    def __init__(
        self,
        db: Session,
        llm_client: Optional[BaseLLMClient] = None,
        evidence_validator: Optional[EvidenceValidator] = None,
        embedding_service: Optional[EmbeddingService] = None,
        temporal_reasoning: Optional[TemporalReasoningService] = None,
        extraction_version: str = "1.0.0",
        window_size: int = 25,
        window_overlap: int = 5,
    ) -> None:
        self.db = db
        self.llm = llm_client or get_llm_client()
        self.validator = evidence_validator or get_evidence_validator()
        self.embedding_service = embedding_service or get_embedding_service()
        self.temporal = temporal_reasoning or TemporalReasoningService(db=self.db)
        self.extraction_version = extraction_version
        self.window_size = window_size
        self.window_overlap = window_overlap

    def extract_memories_for_meeting(
        self,
        meeting_id: uuid.UUID,
        force: bool = False,
    ) -> MemoryExtractionRun:
        """Extract validated temporal memories for a single meeting."""
        meeting = self.db.get(Meeting, meeting_id)
        if not meeting:
            raise MemoryExtractionError(f"Meeting with ID '{meeting_id}' not found.")

        meeting_code = meeting.meeting_code
        team_code = meeting.team.team_code

        # Check existing run for idempotency
        existing_run = (
            self.db.execute(
                select(MemoryExtractionRun)
                .where(
                    MemoryExtractionRun.meeting_id == meeting.id,
                    MemoryExtractionRun.status == "COMPLETED",
                )
                .order_by(MemoryExtractionRun.completed_at.desc())
            )
            .scalars()
            .first()
        )

        if existing_run and not force:
            logger.info(
                f"Meeting {meeting_code} already processed in run {existing_run.id}. Skipping (force=False)."
            )
            return existing_run

        # If force re-run: remove prior memories for this meeting cleanly
        if force:
            logger.info(
                f"Force re-extraction requested for meeting {meeting_code}. Clearing previous memories."
            )
            prior_memories = (
                self.db.execute(select(Memory).where(Memory.meeting_id == meeting.id))
                .scalars()
                .all()
            )
            for mem in prior_memories:
                self.db.delete(mem)
            self.db.flush()

        # Create extraction run record
        run = MemoryExtractionRun(
            id=uuid.uuid4(),
            team_id=meeting.team_id,
            meeting_id=meeting.id,
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            total_turns_analyzed=0,
            total_memories_extracted=0,
            total_memories_validated=0,
            total_memories_rejected=0,
            total_relationships_created=0,
            errors_json=[],
            summary_json={},
        )
        self.db.add(run)
        self.db.flush()

        errors_list: List[Dict[str, Any]] = []

        try:
            with self.db.begin_nested():
                # Query all turns in order
                turns = (
                    self.db.execute(
                        select(TranscriptTurn)
                        .where(TranscriptTurn.meeting_id == meeting.id)
                        .order_by(TranscriptTurn.turn_index.asc())
                    )
                    .scalars()
                    .all()
                )

                run.total_turns_analyzed = len(turns)
                turns_by_index = {t.turn_index: t for t in turns}

                if not turns:
                    run.status = "COMPLETED"
                    run.completed_at = datetime.now(timezone.utc)
                    self.db.commit()
                    return run

                step = max(1, self.window_size - self.window_overlap)
                seen_quotes = set()

                for start_idx in range(0, len(turns), step):
                    chunk_turns = turns[start_idx : start_idx + self.window_size]
                    if not chunk_turns:
                        break

                    # Build prompt for chunk
                    turns_text_list = []
                    for t in chunk_turns:
                        spk = t.speaker.speaker_label if t.speaker else f"Speaker {t.turn_index}"
                        turns_text_list.append(
                            f"[Turn {t.turn_index}] {spk} ({t.start_time_str}): {t.raw_text}"
                        )
                    turns_block = "\n".join(turns_text_list)

                    prompt = (
                        f"Team: {team_code}\n"
                        f"Meeting: {meeting_code} (Meeting #{meeting.meeting_number}, sequence '{meeting.sequence_letter}')\n\n"
                        f"TRANSCRIPT TURNS:\n{turns_block}\n\n"
                        f"Extract memory items adhering to all guidelines:"
                    )

                    try:
                        response_json = self.llm.generate_json(
                            prompt=prompt,
                            system_prompt=EXTRACTION_SYSTEM_PROMPT,
                        )
                    except Exception as e:
                        logger.warning(
                            f"LLM extraction error on window starting at {start_idx}: {e}"
                        )
                        errors_list.append({"window_start": start_idx, "error": str(e)})
                        continue

                    candidate_list = response_json.get("memories", [])
                    if not isinstance(candidate_list, list):
                        continue

                    for cand in candidate_list:
                        run.total_memories_extracted += 1
                        raw_quote = cand.get("quote", "").strip()
                        speaker_label = cand.get("speaker_label", "").strip()
                        cand_turn_idx = cand.get("turn_index")
                        memory_type_str = cand.get("memory_type", "").upper()
                        statement = cand.get("statement", "").strip()

                        if (
                            not raw_quote
                            or not statement
                            or memory_type_str not in MemoryType.__members__
                        ):
                            run.total_memories_rejected += 1
                            errors_list.append(
                                {
                                    "candidate": cand,
                                    "reason": "Missing statement/quote or invalid memory type.",
                                }
                            )
                            continue

                        # Deduplicate within meeting
                        norm_quote_key = raw_quote.lower()
                        if norm_quote_key in seen_quotes:
                            continue
                        seen_quotes.add(norm_quote_key)

                        # Locate supporting turn
                        turn = turns_by_index.get(cand_turn_idx)
                        if not turn:
                            # Fallback: search chunk turns for verbatim quote match
                            norm_q = raw_quote.lower()
                            for ct in chunk_turns:
                                if norm_q in ct.raw_text.lower():
                                    turn = ct
                                    cand_turn_idx = ct.turn_index
                                    break

                        if not turn:
                            run.total_memories_rejected += 1
                            errors_list.append(
                                {
                                    "candidate": cand,
                                    "reason": f"Referenced turn index {cand_turn_idx} not found.",
                                }
                            )
                            continue

                        # Evidence validation
                        metadata = cand.get("metadata", {}) or {}
                        owner = metadata.get("owner")
                        is_valid, reject_reason = self.validator.validate_memory_evidence(
                            quote=raw_quote,
                            speaker_label=speaker_label,
                            turn=turn,
                            owner=owner,
                        )

                        if not is_valid:
                            run.total_memories_rejected += 1
                            errors_list.append(
                                {
                                    "candidate": cand,
                                    "turn_index": cand_turn_idx,
                                    "reason": reject_reason,
                                }
                            )
                            continue

                        # Candidate passed all checks: persist valid memory
                        run.total_memories_validated += 1

                        # Generate statement vector embedding
                        try:
                            embeddings = self.embedding_service.generate_embeddings([statement])
                            stmt_vec = embeddings[0] if embeddings else None
                        except Exception as e:
                            logger.warning(
                                f"Failed to generate embedding for memory statement: {e}"
                            )
                            stmt_vec = None

                        # Set initial lifecycle status
                        initial_status = MemoryStatus.CURRENT.value
                        if memory_type_str == MemoryType.DISAGREEMENT.value:
                            initial_status = MemoryStatus.OPEN.value
                        elif memory_type_str == MemoryType.ACTION.value:
                            initial_status = MemoryStatus.OPEN.value

                        memory = Memory(
                            id=uuid.uuid4(),
                            team_id=meeting.team_id,
                            meeting_id=meeting.id,
                            turn_id=turn.id,
                            memory_type=memory_type_str,
                            statement=statement,
                            quote=raw_quote,
                            speaker_label=speaker_label,
                            speaker_role=turn.speaker.role if turn.speaker else None,
                            meeting_order=meeting.meeting_number or 1,
                            sequence_letter=meeting.sequence_letter or "a",
                            status=initial_status,
                            confidence=float(cand.get("confidence", 1.0)),
                            extraction_version=self.extraction_version,
                            embedding=stmt_vec,
                            metadata_json=metadata,
                        )
                        self.db.add(memory)
                        self.db.flush()

                        # Connect temporal relationships
                        rel_type = cand.get("relationship_type")
                        rel_rationale = cand.get("relationship_rationale")
                        is_ambiguous = bool(cand.get("is_ambiguous", False))

                        created_rels = self.temporal.link_memory_to_prior_memories(
                            new_memory=memory,
                            candidate_rel=rel_type,
                            rationale=rel_rationale,
                            is_ambiguous=is_ambiguous,
                        )
                        run.total_relationships_created += len(created_rels)

            run.status = "COMPLETED"
            run.completed_at = datetime.now(timezone.utc)
            run.errors_json = list(errors_list)
            run.summary_json = {
                "meeting_code": meeting_code,
                "team_code": team_code,
                "total_turns": run.total_turns_analyzed,
                "extracted": run.total_memories_extracted,
                "validated": run.total_memories_validated,
                "rejected": run.total_memories_rejected,
                "relationships_created": run.total_relationships_created,
            }
            self.db.commit()
            return run

        except Exception as e:
            run.status = "FAILED"
            run.completed_at = datetime.now(timezone.utc)
            errors_list.append({"fatal_error": str(e)})
            run.errors_json = list(errors_list)
            self.db.commit()
            logger.error(f"Memory extraction failed for meeting {meeting_code}: {e}")
            raise MemoryExtractionError(f"Memory extraction failed: {e}") from e

    def extract_memories_for_team(
        self,
        team_code: str,
        force: bool = False,
    ) -> List[MemoryExtractionRun]:
        """Process an entire team series in chronological order (a -> b -> c -> d)."""
        team = self.db.execute(select(Team).where(Team.team_code == team_code)).scalar_one_or_none()

        if not team:
            raise MemoryExtractionError(f"Team with code '{team_code}' not found.")

        meetings = (
            self.db.execute(
                select(Meeting)
                .where(Meeting.team_id == team.id)
                .order_by(Meeting.meeting_number.asc(), Meeting.sequence_letter.asc())
            )
            .scalars()
            .all()
        )

        runs: List[MemoryExtractionRun] = []
        for mtg in meetings:
            logger.info(f"Extracting memories for team {team_code}, meeting {mtg.meeting_code}...")
            run = self.extract_memories_for_meeting(meeting_id=mtg.id, force=force)
            runs.append(run)

        return runs
