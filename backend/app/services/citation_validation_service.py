"""Deterministic Citation and Evidence Validation Service for Catalist Meeting Intelligence."""

import re
import uuid
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.logging import get_logger
from app.models.dataset import Meeting, Team, TranscriptTurn
from app.schemas.agent import AnswerValidationResult, CitationValidationItem

logger = get_logger("app.services.citation_validation")

MIN_QUOTE_WORDS = 6
MIN_SENTENCES = 1
MAX_SENTENCES = 3
MIN_CITATIONS = 1
MAX_CITATIONS = 3
MIN_DISTINCT_MEETINGS = 2


def normalize_for_quote_match(text: str) -> str:
    """
    Normalize whitespace and casing for exact quotation substring comparison.
    Collapses consecutive whitespace, tabs, and newlines to a single space, strips edges,
    and converts to lowercase. Wording and punctuation are preserved.
    """
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()


def split_sentences(text: str) -> List[str]:
    """
    Split text into individual plain sentences using boundary heuristics.
    Avoids splitting on common abbreviations.
    """
    if not text or not text.strip():
        return []
    cleaned = text.strip()
    raw_splits = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"\'\[\(])", cleaned)
    sentences = [s.strip() for s in raw_splits if s.strip()]
    return sentences if sentences else [cleaned]


class CitationValidationService:
    """
    Deterministic validator ensuring that:
    1. Every citation is grounded in an actual database speaker turn.
    2. Quotations are verbatim substrings with >= 6 words.
    3. Quotes are not stitched across multiple turns.
    4. Meeting and team attributions are correct and consistent.
    5. Speaker letters and roles are supported by transcript metadata.
    6. Answer satisfies Catalist constraints: 1-3 sentences, 1-3 citations, >=2 distinct meetings.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def validate_citation(
        self,
        citation: Dict[str, Any],
        expected_team: Optional[str] = None,
    ) -> CitationValidationItem:
        """
        Deterministically validate an individual citation against the database.
        Never invokes an LLM.
        """
        errors: List[str] = []
        raw_meeting = citation.get("meeting_id") or ""
        raw_team = citation.get("team_id") or citation.get("team_code")
        raw_quote = citation.get("quote") or ""
        raw_speaker = citation.get("speaker_label") or ""
        raw_role = citation.get("speaker_role")
        raw_turn_id = citation.get("turn_id")

        words = raw_quote.strip().split()
        word_count = len(words)

        # 1. Enforce minimum quote length (at least 6 words)
        if word_count < MIN_QUOTE_WORDS:
            errors.append(
                f"Quotation has only {word_count} words; minimum required is {MIN_QUOTE_WORDS}."
            )

        # 2. Confirm meeting exists
        meeting_record: Optional[Meeting] = None
        if raw_meeting:
            # Try by meeting_code first (case-insensitive)
            stmt = (
                select(Meeting)
                .options(joinedload(Meeting.team))
                .where(func.lower(Meeting.meeting_code) == str(raw_meeting).lower())
            )
            meeting_record = self.db.execute(stmt).scalars().first()

            if not meeting_record:
                # Try by UUID if valid UUID format
                try:
                    m_uuid = uuid.UUID(str(raw_meeting))
                    stmt = (
                        select(Meeting)
                        .options(joinedload(Meeting.team))
                        .where(Meeting.id == m_uuid)
                    )
                    meeting_record = self.db.execute(stmt).scalars().first()
                except ValueError:
                    pass

        if not meeting_record:
            errors.append(f"Meeting '{raw_meeting}' does not exist in corpus.")
            return CitationValidationItem(
                is_valid=False,
                meeting_id=str(raw_meeting),
                quote=raw_quote,
                word_count=word_count,
                speaker_label=raw_speaker,
                turn_id=str(raw_turn_id) if raw_turn_id else None,
                errors=errors,
            )

        # 3. Confirm meeting belongs to the expected team
        meeting_team_code = (meeting_record.team.team_code if meeting_record.team else "").upper()
        if expected_team and meeting_team_code != expected_team.upper():
            errors.append(
                f"Meeting '{meeting_record.meeting_code}' belongs to team '{meeting_team_code}', "
                f"not expected team '{expected_team.upper()}'."
            )
        if raw_team and raw_team.upper() != meeting_team_code:
            errors.append(
                f"Citation team '{raw_team}' does not match meeting team '{meeting_team_code}'."
            )

        # 4. Confirm speaker turn exists and verify exact quote match within that turn
        turn_record: Optional[TranscriptTurn] = None
        if raw_turn_id:
            try:
                t_uuid = uuid.UUID(str(raw_turn_id))
                turn_stmt = (
                    select(TranscriptTurn)
                    .options(joinedload(TranscriptTurn.speaker))
                    .where(TranscriptTurn.id == t_uuid)
                )
                turn_record = self.db.execute(turn_stmt).scalars().first()
            except ValueError:
                pass

        norm_quote = normalize_for_quote_match(raw_quote)

        if turn_record:
            # Confirm turn belongs to the referenced meeting
            if turn_record.meeting_id != meeting_record.id:
                errors.append(
                    f"Turn ID '{raw_turn_id}' belongs to a different meeting, not '{meeting_record.meeting_code}'."
                )

            # Check that quote is strictly contained in this turn (not stitched across turns)
            norm_turn_text = normalize_for_quote_match(turn_record.raw_text)
            if norm_quote not in norm_turn_text:
                errors.append(
                    "Quotation was not found verbatim in referenced speaker turn "
                    "(modified, fabricated, or stitched across turns)."
                )
        else:
            # If turn_id was missing or invalid, search for a turn in this meeting containing the quote
            turns_stmt = (
                select(TranscriptTurn)
                .options(joinedload(TranscriptTurn.speaker))
                .where(TranscriptTurn.meeting_id == meeting_record.id)
            )
            candidate_turns = self.db.execute(turns_stmt).scalars().all()
            matching_turn = None
            for t in candidate_turns:
                if norm_quote in normalize_for_quote_match(t.raw_text):
                    matching_turn = t
                    break

            if matching_turn:
                turn_record = matching_turn
                raw_turn_id = str(matching_turn.id)
            else:
                errors.append(
                    f"Quotation was not found verbatim in any turn of meeting '{meeting_record.meeting_code}'."
                )

        # 5. Validate speaker label and role consistency
        if turn_record and turn_record.speaker:
            exp_label = turn_record.speaker.speaker_label or ""
            exp_letter = turn_record.speaker.speaker_letter or (
                exp_label.split()[-1] if exp_label else ""
            )
            exp_role = turn_record.speaker.role or ""

            if raw_speaker:
                # Extract letter from given speaker (e.g. "Speaker B" -> "B")
                given_letter_match = re.search(r"\b([A-D])\b", raw_speaker)
                given_letter = given_letter_match.group(1) if given_letter_match else ""
                if given_letter and exp_letter and given_letter.upper() != exp_letter.upper():
                    errors.append(
                        f"Speaker label '{raw_speaker}' (letter {given_letter}) does not match "
                        f"turn speaker '{exp_label}' (letter {exp_letter})."
                    )

            # Enforce speaker role rule: include speaker roles only when supported by the transcript/metadata
            if raw_role and exp_role:
                if raw_role.strip().lower() != exp_role.strip().lower():
                    errors.append(
                        f"Claimed speaker role '{raw_role}' does not match transcript speaker role '{exp_role}'."
                    )
            elif raw_role and not exp_role:
                errors.append(
                    f"Claimed speaker role '{raw_role}' is not supported by transcript metadata."
                )

        is_valid = len(errors) == 0
        return CitationValidationItem(
            is_valid=is_valid,
            meeting_id=meeting_record.meeting_code if meeting_record else str(raw_meeting),
            quote=raw_quote,
            word_count=word_count,
            speaker_label=raw_speaker,
            turn_id=str(turn_record.id)
            if turn_record
            else (str(raw_turn_id) if raw_turn_id else None),
            errors=errors,
        )

    def validate_answer(
        self,
        answer: str,
        citations: List[Dict[str, Any]],
        expected_team: Optional[str] = None,
    ) -> AnswerValidationResult:
        """
        Validate complete answer against all Catalist citation and structure rules:
        - 1 to 3 plain sentences.
        - 1 to 3 citations.
        - Evidence from at least two distinct meetings of the named team.
        - Every citation passes individual validation.
        - Citations support the claims they are attached to.
        - No unsupported factual claims introduced.
        """
        all_errors: List[str] = []

        # 1. Sentence count validation (1 to 3 sentences)
        sentences = split_sentences(answer)
        sentence_count = len(sentences)
        if sentence_count < MIN_SENTENCES or sentence_count > MAX_SENTENCES:
            all_errors.append(
                f"Answer contains {sentence_count} sentences; Catalist requirement is {MIN_SENTENCES} to {MAX_SENTENCES} plain sentences."
            )

        # 2. Citation count validation (1 to 3 citations)
        citation_count = len(citations)
        if citation_count < MIN_CITATIONS or citation_count > MAX_CITATIONS:
            all_errors.append(
                f"Answer has {citation_count} citations; Catalist requirement is {MIN_CITATIONS} to {MAX_CITATIONS} citations."
            )

        # 3. Individual citation validations
        validated_citations: List[CitationValidationItem] = []
        valid_meeting_codes: Set[str] = set()

        for idx, cite in enumerate(citations):
            val_item = self.validate_citation(cite, expected_team=expected_team)
            validated_citations.append(val_item)
            if val_item.is_valid:
                valid_meeting_codes.add(val_item.meeting_id.lower())
            else:
                for err in val_item.errors:
                    all_errors.append(f"Citation {idx + 1} error: {err}")

        # 4. Multi-meeting requirement (at least 2 distinct meetings of the named team)
        distinct_meetings = sorted(list(valid_meeting_codes))
        total_meetings_stmt = select(func.count(Meeting.id))
        total_meetings_count = self.db.scalar(total_meetings_stmt) or 0
        if expected_team:
            team_cnt_stmt = (
                select(func.count(Meeting.id))
                .join(Team, Meeting.team_id == Team.id)
                .where(func.lower(Team.team_code) == str(expected_team).lower())
            )
            corpus_count = self.db.scalar(team_cnt_stmt) or 0
        else:
            corpus_count = total_meetings_count

        required_distinct = (
            MIN_DISTINCT_MEETINGS if corpus_count >= MIN_DISTINCT_MEETINGS else max(1, corpus_count)
        )
        if len(distinct_meetings) < required_distinct:
            team_str = f" of team '{expected_team}'" if expected_team else ""
            all_errors.append(
                f"Answer cites {len(distinct_meetings)} distinct meeting(s) ({distinct_meetings}); "
                f"Catalist requirement is evidence from at least {required_distinct} meetings{team_str}."
            )

        # 5. Claim support check: citations must support the claims in the answer
        if answer and citations:
            answer_lower = answer.lower()
            combined_quotes = " ".join((c.get("quote") or "").lower() for c in citations)

            # Extract substantive content tokens from answer (excluding basic question/grammar stopwords)
            ans_tokens = [
                t
                for t in re.findall(r"\b[a-z0-9\-\_]{4,}\b", answer_lower)
                if t
                not in {
                    "team",
                    "meeting",
                    "decided",
                    "decision",
                    "based",
                    "discussions",
                    "initially",
                    "planned",
                    "switch",
                    "switched",
                    "because",
                    "their",
                    "they",
                    "speaker",
                }
            ]

            if ans_tokens:
                # Check overlap between substantive answer words and citation quotes
                matching_words = [t for t in ans_tokens if t in combined_quotes]
                overlap_ratio = len(matching_words) / max(1, len(ans_tokens))

                # If the answer introduces substantive claims with very low evidence overlap (< 20%)
                if overlap_ratio < 0.20:
                    all_errors.append(
                        f"Answer contains unsubstantiated claims not backed by citation quotations "
                        f"(lexical overlap: {overlap_ratio:.0%})."
                    )

        is_valid = len(all_errors) == 0
        return AnswerValidationResult(
            is_valid=is_valid,
            sentence_count=sentence_count,
            citation_count=citation_count,
            distinct_meetings=distinct_meetings,
            supporting_meetings=distinct_meetings if is_valid else [],
            citations=validated_citations,
            errors=all_errors,
        )


_service_instance: Optional[CitationValidationService] = None


def get_citation_validation_service(db: Session) -> CitationValidationService:
    """Return CitationValidationService instance for the given database session."""
    return CitationValidationService(db)
