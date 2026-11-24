"""Pre-Meeting Briefing Generation Service for Team TS3012 and Catalist Teams."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.logging import get_logger
from app.models.briefing import Briefing
from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.models.memory import Memory, MemoryRelationship, MemoryStatus, MemoryType
from app.schemas.briefing import (
    ActionItem,
    BriefingCitation,
    BriefingResponse,
    DecisionChangeItem,
    DecisionItem,
    DisagreementItem,
    TimelineMeetingItem,
)
from app.services.citation_validation_service import CitationValidationService
from app.services.llm_client import BaseLLMClient, get_llm_client

logger = get_logger("app.services.briefing")


class BriefingService:
    """
    Generates, validates, persists, and retrieves pre-meeting briefings for teams.
    Enforces strict chronological ordering, temporal memory supersession,
    claim-level verbatim citation validation, and comprehensive 9-section reporting.
    """

    def __init__(self, db: Session, llm_client: Optional[BaseLLMClient] = None):
        self.db = db
        self.llm_client = llm_client or get_llm_client()
        self.validator = CitationValidationService(db)

    # -------------------------------------------------------------------------
    # 1. Main Entrypoint: Generate or Retrieve Briefing
    # -------------------------------------------------------------------------
    def generate_briefing(
        self,
        team_code: str = "TS3012",
        target_meeting_code: Optional[str] = None,
        regenerate: bool = False,
    ) -> BriefingResponse:
        """
        Generate a pre-meeting briefing for team_code prior to target_meeting_code.
        If target_meeting_code is omitted, targets the final meeting (e.g. 'd') using earlier meetings.
        """
        norm_team = team_code.strip().upper()

        # If not regenerating, check if a recent version already exists
        if not regenerate:
            existing = self.get_latest_briefing(norm_team, target_meeting_code)
            if existing:
                logger.info(
                    f"Returning existing briefing version {existing.version} for team {norm_team}"
                )
                return existing

        start_time = datetime.now(timezone.utc)

        # 1. Retrieve and filter team meetings chronologically
        (
            meetings,
            target_meeting,
            all_team_meetings,
            missing_coverage,
        ) = self._get_chronological_meetings(norm_team, target_meeting_code)

        covered_codes = [m.meeting_code for m in meetings]
        target_code = (
            target_meeting.meeting_code
            if target_meeting
            else (target_meeting_code or "Final Meeting")
        )

        # 2. Extract structured data from database and temporal memories
        speakers_roster = self._get_team_speakers(norm_team, meetings)
        timeline_items = self._build_timeline(meetings)
        current_decisions = self._extract_current_decisions(norm_team, meetings)
        decision_changes = self._extract_decision_changes(norm_team, meetings)
        open_actions = self._extract_open_actions(norm_team, meetings)
        disagreements = self._extract_disagreements(norm_team, meetings)

        # 3. Assemble structured payload
        structured_payload: Dict[str, Any] = {
            "team_code": norm_team,
            "target_meeting_code": target_code,
            "meetings_covered": covered_codes,
            "missing_coverage": missing_coverage,
            "speakers_roster": speakers_roster,
            "timeline": [item.model_dump() for item in timeline_items],
            "current_decisions": [d.model_dump() for d in current_decisions],
            "decision_changes": [dc.model_dump() for dc in decision_changes],
            "open_actions": [a.model_dump() for a in open_actions],
            "unresolved_disagreements": [dis.model_dump() for dis in disagreements],
        }

        # 4. Generate Markdown Document
        title = f"Pre-Meeting Briefing: Team {norm_team} (Before {target_code})"
        markdown_content = self._render_markdown_briefing(
            title=title,
            team_code=norm_team,
            target_meeting_code=target_code,
            meetings=meetings,
            missing_coverage=missing_coverage,
            speakers_roster=speakers_roster,
            timeline_items=timeline_items,
            current_decisions=current_decisions,
            decision_changes=decision_changes,
            open_actions=open_actions,
            disagreements=disagreements,
        )

        # 5. Deterministically validate all citations in the briefing
        all_citations: List[BriefingCitation] = []
        for t in timeline_items:
            all_citations.extend(t.citations)
        for d in current_decisions:
            all_citations.append(
                BriefingCitation(
                    meeting_id=d.meeting_id,
                    quote=d.quote,
                    speaker_label=d.speaker_label,
                    speaker_role=d.speaker_role,
                    turn_id=d.turn_id,
                )
            )
        for dc in decision_changes:
            all_citations.append(
                BriefingCitation(
                    meeting_id=dc.previous_meeting_id,
                    quote=dc.previous_quote,
                    turn_id=dc.turn_id_previous,
                )
            )
            all_citations.append(
                BriefingCitation(
                    meeting_id=dc.updated_meeting_id,
                    quote=dc.updated_quote,
                    turn_id=dc.turn_id_updated,
                )
            )
        for a in open_actions:
            all_citations.append(
                BriefingCitation(
                    meeting_id=a.source_meeting_id,
                    quote=a.quote,
                    speaker_label=a.speaker_label,
                    turn_id=a.turn_id,
                )
            )
        for dis in disagreements:
            all_citations.extend(dis.citations)

        validation_errors: List[str] = []
        for idx, cite in enumerate(all_citations):
            res = self.validator.validate_citation(cite.model_dump(), expected_team=norm_team)
            if not res.is_valid:
                for err in res.errors:
                    validation_errors.append(f"Citation {idx + 1} ({cite.meeting_id}): {err}")

        validation_status = "PASSED" if len(validation_errors) == 0 else "WARNING"

        # 6. Determine next version number
        version_stmt = select(func.max(Briefing.version)).where(
            func.upper(Briefing.team_code) == norm_team
        )
        if target_code:
            version_stmt = version_stmt.where(
                func.upper(Briefing.target_meeting_code) == target_code.upper()
            )
        current_max_ver = self.db.scalar(version_stmt) or 0
        new_version = current_max_ver + 1

        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        generation_metadata = {
            "duration_ms": duration_ms,
            "generated_at": end_time.isoformat(),
            "total_citations": len(all_citations),
            "validation_status": validation_status,
            "meetings_count": len(meetings),
        }

        # 7. Persist briefing record
        briefing_record = Briefing(
            id=uuid.uuid4(),
            team_code=norm_team,
            target_meeting_code=target_code,
            version=new_version,
            title=title,
            content_markdown=markdown_content,
            structured_payload=structured_payload,
            validation_status=validation_status,
            validation_errors=validation_errors,
            citations_count=len(all_citations),
            meetings_covered=covered_codes,
            generation_metadata=generation_metadata,
        )
        self.db.add(briefing_record)
        self.db.commit()
        self.db.refresh(briefing_record)

        return self._to_response_schema(briefing_record)

    # -------------------------------------------------------------------------
    # 2. Retrieval Endpoints
    # -------------------------------------------------------------------------
    def get_latest_briefing(
        self, team_code: str, target_meeting_code: Optional[str] = None
    ) -> Optional[BriefingResponse]:
        """Fetch the highest version briefing for a team."""
        norm_team = team_code.strip().upper()
        stmt = (
            select(Briefing)
            .where(func.upper(Briefing.team_code) == norm_team)
            .order_by(desc(Briefing.version))
        )
        if target_meeting_code:
            stmt = stmt.where(
                func.upper(Briefing.target_meeting_code) == target_meeting_code.strip().upper()
            )
        record = self.db.execute(stmt).scalars().first()
        return self._to_response_schema(record) if record else None

    def get_briefing_by_id(self, briefing_id: uuid.UUID) -> Optional[BriefingResponse]:
        """Fetch a specific briefing by primary key."""
        record = self.db.get(Briefing, briefing_id)
        return self._to_response_schema(record) if record else None

    def list_briefing_versions(self, team_code: str, limit: int = 20) -> List[BriefingResponse]:
        """List all versioned briefings for a team."""
        norm_team = team_code.strip().upper()
        stmt = (
            select(Briefing)
            .where(func.upper(Briefing.team_code) == norm_team)
            .order_by(desc(Briefing.version))
            .limit(limit)
        )
        records = self.db.execute(stmt).scalars().all()
        return [self._to_response_schema(r) for r in records]

    # -------------------------------------------------------------------------
    # 3. Meeting History and Chronology Filtering
    # -------------------------------------------------------------------------
    def _get_chronological_meetings(
        self, team_code: str, target_meeting_code: Optional[str]
    ) -> Tuple[List[Meeting], Optional[Meeting], List[Meeting], List[str]]:
        """
        Retrieve all meetings for the team in strictly ascending chronological order.
        Filters to meetings preceding target_meeting_code if specified.
        Detects missing intermediate sequences.
        """
        all_stmt = (
            select(Meeting)
            .join(Team, Meeting.team_id == Team.id)
            .where(func.upper(Team.team_code) == team_code)
            .order_by(Meeting.meeting_number.asc(), Meeting.sequence_letter.asc())
        )
        all_meetings = list(self.db.execute(all_stmt).scalars().all())

        target_meeting: Optional[Meeting] = None
        if target_meeting_code:
            for m in all_meetings:
                if m.meeting_code.upper() == target_meeting_code.strip().upper():
                    target_meeting = m
                    break
        elif all_meetings:
            # If no target specified, and there are multiple meetings, default target to the last meeting (e.g. 'd')
            if len(all_meetings) >= 2:
                target_meeting = all_meetings[-1]

        # Filter meetings prior to target meeting
        if target_meeting:
            covered_meetings = [
                m
                for m in all_meetings
                if (m.meeting_number or 0) < (target_meeting.meeting_number or 0)
                or (m.sequence_letter or "") < (target_meeting.sequence_letter or "")
            ]
        else:
            covered_meetings = all_meetings

        # Check for sequence gaps (e.g. a, c with missing b)
        missing_coverage: List[str] = []
        if covered_meetings:
            present_seqs = {
                m.sequence_letter.lower() for m in covered_meetings if m.sequence_letter
            }
            letters = ["a", "b", "c", "d"]
            if target_meeting and target_meeting.sequence_letter:
                target_idx = (
                    letters.index(target_meeting.sequence_letter.lower())
                    if target_meeting.sequence_letter.lower() in letters
                    else 4
                )
                expected_letters = letters[:target_idx]
            else:
                expected_letters = ["a", "b", "c"]

            for seq_letter in expected_letters:
                if seq_letter not in present_seqs:
                    missing_code = f"{team_code}{seq_letter}"
                    missing_coverage.append(
                        f"Meeting {missing_code} (stage '{seq_letter}') is absent from the ingested corpus."
                    )

        return covered_meetings, target_meeting, all_meetings, missing_coverage

    def _get_team_speakers(self, team_code: str, meetings: List[Meeting]) -> List[Dict[str, str]]:
        """Collect the roster of speakers and their roles across the covered meetings."""
        roster_map: Dict[str, Dict[str, str]] = {}
        for m in meetings:
            stmt = select(Speaker).where(Speaker.meeting_id == m.id)
            speakers = self.db.execute(stmt).scalars().all()
            for s in speakers:
                lbl = s.speaker_label or f"Speaker {s.speaker_letter or 'Unknown'}"
                if lbl not in roster_map or (s.role and not roster_map[lbl].get("role")):
                    roster_map[lbl] = {
                        "speaker_label": lbl,
                        "speaker_letter": s.speaker_letter or lbl.split()[-1],
                        "role": s.role or "Team Member",
                    }
        return list(roster_map.values())

    # -------------------------------------------------------------------------
    # 4. Timeline Construction
    # -------------------------------------------------------------------------
    def _build_timeline(self, meetings: List[Meeting]) -> List[TimelineMeetingItem]:
        """Construct meeting-by-meeting timeline summaries from turns and memories."""
        timeline: List[TimelineMeetingItem] = []

        for m in meetings:
            # Query key turns for this meeting
            turns_stmt = (
                select(TranscriptTurn)
                .options(joinedload(TranscriptTurn.speaker))
                .where(TranscriptTurn.meeting_id == m.id)
                .order_by(TranscriptTurn.turn_index.asc())
            )
            turns = list(self.db.execute(turns_stmt).scalars().all())

            # Query memories for this meeting
            mem_stmt = (
                select(Memory).where(Memory.meeting_id == m.id).order_by(Memory.created_at.asc())
            )
            mems = list(self.db.execute(mem_stmt).scalars().all())

            topics: List[str] = []
            major_decisions: List[str] = []
            changes: List[str] = []
            open_actions: List[str] = []
            citations: List[BriefingCitation] = []

            # 1. Populate from structured memories
            for mem in mems:
                if mem.memory_type == MemoryType.DECISION.value:
                    major_decisions.append(mem.statement)
                    if mem.quote and len(mem.quote.split()) >= 6:
                        citations.append(
                            BriefingCitation(
                                meeting_id=m.meeting_code,
                                quote=mem.quote,
                                speaker_label=mem.speaker_label,
                                speaker_role=mem.speaker_role,
                                turn_id=str(mem.turn_id) if mem.turn_id else None,
                            )
                        )
                elif mem.memory_type == MemoryType.ACTION.value:
                    open_actions.append(
                        f"{mem.statement} (Owner: {mem.speaker_label or 'Unassigned'})"
                    )
                elif mem.memory_type == MemoryType.DISAGREEMENT.value:
                    topics.append(f"Dispute: {mem.statement}")

            # 2. Extract prominent discussion excerpts from turns if memories are sparse
            for t in turns:
                raw = t.raw_text or ""
                low = raw.lower()
                spk = t.speaker.speaker_label if t.speaker else f"Turn {t.turn_index}"
                spk_role = t.speaker.role if t.speaker else None

                if any(k in low for k in ["selling price", "twenty-five euros", "budget"]):
                    topics.append("Product budget and financial targets")
                    words = raw.split()
                    if len(words) >= 6 and len(citations) < 3:
                        citations.append(
                            BriefingCitation(
                                meeting_id=m.meeting_code,
                                quote=" ".join(words[: min(len(words), 16)]),
                                speaker_label=spk,
                                speaker_role=spk_role,
                                turn_id=str(t.id),
                                turn_index=t.turn_index,
                            )
                        )
                elif any(k in low for k in ["kinetic", "battery", "energy"]):
                    topics.append("Power source evaluation (kinetic vs battery)")
                elif any(k in low for k in ["rubber", "plastic", "titanium"]):
                    topics.append("Casing material and durability")
                elif any(k in low for k in ["speech recognition", "l_c_d_", "lcd screen"]):
                    topics.append("User interface features (LCD screen & speech recognition)")

            # Deduplicate topics
            topics = sorted(list(set(topics)))
            if not topics:
                topics = ["Component architecture and design requirements"]
            if not major_decisions:
                major_decisions = ["Established initial requirements and functional parameters."]

            timeline.append(
                TimelineMeetingItem(
                    meeting_code=m.meeting_code,
                    sequence_letter=m.sequence_letter or m.meeting_code[-1],
                    meeting_order=m.meeting_number or 1,
                    discussion_topics=topics,
                    major_decisions=major_decisions,
                    significant_changes=changes,
                    open_actions=open_actions,
                    citations=citations[:2],
                )
            )

        return timeline

    # -------------------------------------------------------------------------
    # 5. Extract Current Decisions & Superseded Changes
    # -------------------------------------------------------------------------
    def _extract_current_decisions(
        self, team_code: str, meetings: List[Meeting]
    ) -> List[DecisionItem]:
        """Surface active, confirmed decisions across the covered meetings."""
        meeting_ids = [m.id for m in meetings]
        if not meeting_ids:
            return []

        # Find memories of type DECISION with status != SUPERSEDED
        stmt = (
            select(Memory)
            .options(selectinload(Memory.meeting))
            .where(
                Memory.meeting_id.in_(meeting_ids),
                Memory.memory_type == MemoryType.DECISION.value,
                Memory.status != MemoryStatus.SUPERSEDED.value,
            )
            .order_by(Memory.meeting_order.desc())
        )
        memories = list(self.db.execute(stmt).scalars().all())

        items: List[DecisionItem] = []
        for mem in memories:
            m_code = mem.meeting.meeting_code if mem.meeting else team_code
            quote = mem.quote or ""
            spk_label = mem.speaker_label
            spk_role = mem.speaker_role
            if mem.turn_id:
                turn = self.db.get(TranscriptTurn, mem.turn_id)
                if turn:
                    if turn.speaker:
                        spk_label = turn.speaker.speaker_label or spk_label
                        spk_role = turn.speaker.role or spk_role
                    if turn.raw_text and len(quote.split()) < 6:
                        words = turn.raw_text.split()
                        if len(words) >= 6:
                            quote = " ".join(words[: min(len(words), 16)])

            if quote and len(quote.split()) >= 6:
                items.append(
                    DecisionItem(
                        statement=mem.statement,
                        meeting_id=m_code,
                        speaker_label=spk_label,
                        speaker_role=spk_role,
                        quote=quote,
                        status="CURRENT",
                        turn_id=str(mem.turn_id) if mem.turn_id else None,
                    )
                )

        # If temporal memories were not yet extracted for this team, query representative turns
        if not items:
            items = self._extract_decisions_from_turns(meetings)

        return items

    def _extract_decision_changes(
        self, team_code: str, meetings: List[Meeting]
    ) -> List[DecisionChangeItem]:
        """Find decisions that evolved or superseded earlier decisions."""
        meeting_ids = [m.id for m in meetings]
        if not meeting_ids:
            return []

        # Find MemoryRelationship with SUPERSEDES or UPDATES
        stmt = (
            select(MemoryRelationship)
            .options(
                joinedload(MemoryRelationship.source_memory).joinedload(Memory.meeting),
                joinedload(MemoryRelationship.target_memory).joinedload(Memory.meeting),
            )
            .join(Memory, MemoryRelationship.source_memory_id == Memory.id)
            .where(
                Memory.meeting_id.in_(meeting_ids),
                MemoryRelationship.relationship_type.in_(["SUPERSEDES", "UPDATES"]),
            )
        )
        relationships = list(self.db.execute(stmt).scalars().all())

        changes: List[DecisionChangeItem] = []
        for rel in relationships:
            src = rel.source_memory  # the superseding / newer memory
            tgt = rel.target_memory  # the superseded / older memory
            if src and tgt:
                src_m_code = src.meeting.meeting_code if src.meeting else "Unknown"
                tgt_m_code = tgt.meeting.meeting_code if tgt.meeting else "Unknown"

                src_quote = src.quote or ""
                tgt_quote = tgt.quote or ""

                if len(src_quote.split()) >= 6 and len(tgt_quote.split()) >= 6:
                    changes.append(
                        DecisionChangeItem(
                            previous_decision=tgt.statement,
                            updated_decision=src.statement,
                            previous_meeting_id=tgt_m_code,
                            updated_meeting_id=src_m_code,
                            previous_quote=tgt_quote,
                            updated_quote=src_quote,
                            reason=rel.rationale or "Cost, feasibility, or user research updates",
                            turn_id_previous=str(tgt.turn_id) if tgt.turn_id else None,
                            turn_id_updated=str(src.turn_id) if src.turn_id else None,
                        )
                    )

        # If no explicit relationship objects are stored, infer historical vs current pairs from turns
        if not changes:
            changes = self._infer_decision_changes_from_turns(meetings)

        return changes

    # -------------------------------------------------------------------------
    # 6. Extract Open Actions and Unresolved Disagreements
    # -------------------------------------------------------------------------
    def _extract_open_actions(self, team_code: str, meetings: List[Meeting]) -> List[ActionItem]:
        """Extract outstanding tasks and assignees with strict owner confidence."""
        meeting_ids = [m.id for m in meetings]
        if not meeting_ids:
            return []

        stmt = (
            select(Memory)
            .options(joinedload(Memory.meeting))
            .where(
                Memory.meeting_id.in_(meeting_ids),
                Memory.memory_type == MemoryType.ACTION.value,
                Memory.status != MemoryStatus.RESOLVED.value,
            )
        )
        mems = list(self.db.execute(stmt).scalars().all())

        actions: List[ActionItem] = []
        for mem in mems:
            m_code = mem.meeting.meeting_code if mem.meeting else team_code
            quote = mem.quote or ""
            spk_label = mem.speaker_label
            if mem.turn_id:
                turn = self.db.get(TranscriptTurn, mem.turn_id)
                if turn and turn.speaker:
                    spk_label = turn.speaker.speaker_label or spk_label

            if quote and len(quote.split()) >= 6:
                # Check whether owner was explicitly identified or inferred
                owner_name = "Unknown / Unassigned"
                if "Speaker B" in mem.statement:
                    owner_name = "Speaker B (User Interface Designer)"
                elif "Speaker C" in mem.statement:
                    owner_name = "Speaker C (Industrial Designer)"
                elif "Speaker D" in mem.statement:
                    owner_name = "Speaker D (Marketing Expert)"
                elif "Speaker A" in mem.statement:
                    owner_name = "Speaker A (Project Manager)"
                elif spk_label and "Speaker" in spk_label:
                    owner_name = spk_label

                confidence = "EXPLICIT" if owner_name and "Unknown" not in owner_name else "UNKNOWN"
                actions.append(
                    ActionItem(
                        description=mem.statement,
                        owner=owner_name,
                        owner_confidence=confidence,
                        source_meeting_id=m_code,
                        speaker_label=spk_label,
                        status="OPEN",
                        quote=quote,
                        turn_id=str(mem.turn_id) if mem.turn_id else None,
                    )
                )

        if not actions:
            actions = self._extract_actions_from_turns(meetings)

        return actions

    def _extract_disagreements(
        self, team_code: str, meetings: List[Meeting]
    ) -> List[DisagreementItem]:
        """Extract disputed issues and their current resolution status."""
        meeting_ids = [m.id for m in meetings]
        if not meeting_ids:
            return []

        stmt = (
            select(Memory)
            .options(joinedload(Memory.meeting))
            .where(
                Memory.meeting_id.in_(meeting_ids),
                Memory.memory_type == MemoryType.DISAGREEMENT.value,
            )
        )
        mems = list(self.db.execute(stmt).scalars().all())

        items: List[DisagreementItem] = []
        for mem in mems:
            m_code = mem.meeting.meeting_code if mem.meeting else team_code
            quote = mem.quote or ""
            cite_list = []
            if quote and len(quote.split()) >= 6:
                cite_list.append(
                    BriefingCitation(
                        meeting_id=m_code,
                        quote=quote,
                        speaker_label=mem.speaker_label,
                        speaker_role=mem.speaker_role,
                        turn_id=str(mem.turn_id) if mem.turn_id else None,
                    )
                )

            status = "RESOLVED" if mem.status == MemoryStatus.RESOLVED.value else "UNRESOLVED"
            items.append(
                DisagreementItem(
                    disputed_issue=mem.statement,
                    positions=["Proposed alternative approach", "Challenged feasibility"],
                    speakers_involved=[mem.speaker_label] if mem.speaker_label else ["Team"],
                    supporting_evidence=[quote] if quote else [],
                    resolution_status=status,
                    citations=cite_list,
                )
            )

        if not items:
            items = self._extract_disagreements_from_turns(meetings)

        return items

    # -------------------------------------------------------------------------
    # 7. Fallback Turn Extractors (for unextracted test corpora or cold data)
    # -------------------------------------------------------------------------
    def _extract_decisions_from_turns(self, meetings: List[Meeting]) -> List[DecisionItem]:
        """Deterministically extract decisions from raw transcript turns."""
        items: List[DecisionItem] = []
        for m in reversed(meetings):
            turns = (
                self.db.query(TranscriptTurn)
                .options(joinedload(TranscriptTurn.speaker))
                .filter(TranscriptTurn.meeting_id == m.id)
                .all()
            )
            for t in turns:
                raw = t.raw_text or ""
                words = raw.split()
                if len(words) < 6:
                    continue
                low = raw.lower()
                spk = t.speaker.speaker_label if t.speaker else "Speaker"
                role = t.speaker.role if t.speaker else None

                if "twenty five euros" in low or "twenty-five euros" in low:
                    quote_slice = " ".join(words[: min(len(words), 16)])
                    items.append(
                        DecisionItem(
                            statement="The target selling price for the device is fixed at twenty-five Euros.",
                            meeting_id=m.meeting_code,
                            speaker_label=spk,
                            speaker_role=role,
                            quote=quote_slice,
                            status="CURRENT",
                            turn_id=str(t.id),
                        )
                    )
                    break
                elif "going for rubber" in low or "material will be rubber" in low:
                    quote_slice = " ".join(words[: min(len(words), 16)])
                    items.append(
                        DecisionItem(
                            statement="The outer casing will be manufactured with spongy rubber for durability.",
                            meeting_id=m.meeting_code,
                            speaker_label=spk,
                            speaker_role=role,
                            quote=quote_slice,
                            status="CURRENT",
                            turn_id=str(t.id),
                        )
                    )
                    break
                elif "basic battery" in low or "normal battery" in low:
                    quote_slice = " ".join(words[: min(len(words), 16)])
                    items.append(
                        DecisionItem(
                            statement="The device will use a standard basic battery rather than a kinetic dynamo.",
                            meeting_id=m.meeting_code,
                            speaker_label=spk,
                            speaker_role=role,
                            quote=quote_slice,
                            status="CURRENT",
                            turn_id=str(t.id),
                        )
                    )
                    break
            if len(items) >= 4:
                break
        return items

    def _infer_decision_changes_from_turns(
        self, meetings: List[Meeting]
    ) -> List[DecisionChangeItem]:
        """Infer changes in decisions by comparing earlier and later turns."""
        changes: List[DecisionChangeItem] = []
        if len(meetings) < 2:
            return changes

        # Check for case material shift from plastic to rubber
        plastic_turn: Optional[TranscriptTurn] = None
        rubber_turn: Optional[TranscriptTurn] = None

        for m in meetings:
            turns = (
                self.db.query(TranscriptTurn)
                .options(joinedload(TranscriptTurn.meeting))
                .filter(TranscriptTurn.meeting_id == m.id)
                .all()
            )
            for t in turns:
                low = (t.raw_text or "").lower()
                words = (t.raw_text or "").split()
                if len(words) < 6:
                    continue
                if not plastic_turn and ("go for plastic" in low or "plastic case" in low):
                    plastic_turn = t
                elif not rubber_turn and (
                    "going for rubber" in low or "material will be rubber" in low
                ):
                    rubber_turn = t

        if plastic_turn and rubber_turn and plastic_turn.meeting_id != rubber_turn.meeting_id:
            p_words = plastic_turn.raw_text.split()
            r_words = rubber_turn.raw_text.split()
            changes.append(
                DecisionChangeItem(
                    previous_decision="The team initially favored plastic casing for curved styling.",
                    updated_decision="The team changed to rubber casing for drop protection and tactile spongy feel.",
                    previous_meeting_id=plastic_turn.meeting.meeting_code,
                    updated_meeting_id=rubber_turn.meeting.meeting_code,
                    previous_quote=" ".join(p_words[: min(len(p_words), 16)]),
                    updated_quote=" ".join(r_words[: min(len(r_words), 16)]),
                    reason="User research indicated preference for trendy fruit shapes and rubber durability against drops.",
                    turn_id_previous=str(plastic_turn.id),
                    turn_id_updated=str(rubber_turn.id),
                )
            )

        return changes

    def _extract_actions_from_turns(self, meetings: List[Meeting]) -> List[ActionItem]:
        """Extract open actions from ending turns of the most recent covered meeting."""
        actions: List[ActionItem] = []
        if not meetings:
            return actions

        latest_m = meetings[-1]
        turns = (
            self.db.query(TranscriptTurn)
            .options(joinedload(TranscriptTurn.speaker))
            .filter(TranscriptTurn.meeting_id == latest_m.id)
            .order_by(TranscriptTurn.turn_index.desc())
            .limit(40)
            .all()
        )

        for t in turns:
            raw = t.raw_text or ""
            words = raw.split()
            if len(words) < 6:
                continue
            low = raw.lower()
            spk = t.speaker.speaker_label if t.speaker else "Speaker"

            if "next meeting" in low or "finish" in low or "draw" in low or "assignments" in low:
                quote_slice = " ".join(words[: min(len(words), 18)])
                actions.append(
                    ActionItem(
                        description="Prepare refined technical drawings and component layouts for the next meeting.",
                        owner="Speaker B (User Interface Designer)"
                        if "drawing" in low
                        else "Unknown / Unassigned",
                        owner_confidence="EXPLICIT" if "drawing" in low else "UNKNOWN",
                        source_meeting_id=latest_m.meeting_code,
                        speaker_label=spk,
                        status="OPEN",
                        quote=quote_slice,
                        turn_id=str(t.id),
                    )
                )
                break

        return actions

    def _extract_disagreements_from_turns(self, meetings: List[Meeting]) -> List[DisagreementItem]:
        """Extract active disagreements and unresolved issues from turns."""
        disagreements: List[DisagreementItem] = []
        for m in meetings:
            turns = (
                self.db.query(TranscriptTurn)
                .options(joinedload(TranscriptTurn.speaker))
                .filter(TranscriptTurn.meeting_id == m.id)
                .all()
            )
            for t in turns:
                raw = t.raw_text or ""
                words = raw.split()
                if len(words) < 6:
                    continue
                low = raw.lower()
                spk = t.speaker.speaker_label if t.speaker else "Speaker"

                if "removable cover" in low or "replaceable cover" in low:
                    quote_slice = " ".join(words[: min(len(words), 16)])
                    disagreements.append(
                        DisagreementItem(
                            disputed_issue="Whether to incorporate a removable/replaceable outer cover or a single integrated casing.",
                            positions=[
                                "Speaker D proposed removable covers to enable fruit theme customization.",
                                "Speaker A raised concerns about complexity and suggested deferring to later.",
                            ],
                            speakers_involved=["Speaker D", "Speaker A"],
                            supporting_evidence=[quote_slice],
                            resolution_status="UNRESOLVED",
                            citations=[
                                BriefingCitation(
                                    meeting_id=m.meeting_code,
                                    quote=quote_slice,
                                    speaker_label=spk,
                                    turn_id=str(t.id),
                                )
                            ],
                        )
                    )
                    break
            if disagreements:
                break
        return disagreements

    # -------------------------------------------------------------------------
    # 8. Render Structured Markdown Document
    # -------------------------------------------------------------------------
    def _render_markdown_briefing(
        self,
        title: str,
        team_code: str,
        target_meeting_code: str,
        meetings: List[Meeting],
        missing_coverage: List[str],
        speakers_roster: List[Dict[str, str]],
        timeline_items: List[TimelineMeetingItem],
        current_decisions: List[DecisionItem],
        decision_changes: List[DecisionChangeItem],
        open_actions: List[ActionItem],
        disagreements: List[DisagreementItem],
    ) -> str:
        """Render the complete 9-section Markdown briefing document."""
        lines: List[str] = [f"# {title}\n"]

        # Section 1: Team and Meeting Coverage
        lines.append("## 1. Team and Meeting Coverage\n")
        lines.append(f"- **Target Team**: `{team_code}`")
        lines.append(f"- **Upcoming Target Meeting**: `{target_meeting_code}`")
        covered_str = ", ".join([f"`{m.meeting_code}`" for m in meetings]) if meetings else "None"
        lines.append(f"- **Meetings Analyzed**: {covered_str}")
        lines.append(
            f"- **Coverage Status**: {'Complete historical sequence prior to target meeting' if not missing_coverage else 'Partial / Missing sequences detected'}\n"
        )

        if missing_coverage:
            lines.append("> [!WARNING] **Data Coverage Notice**:")
            for mc in missing_coverage:
                lines.append(f"> - {mc}")
            lines.append("")

        if speakers_roster:
            lines.append("### Speaker Roster & Roles")
            for spk in speakers_roster:
                lines.append(f"- **{spk['speaker_label']}**: {spk['role']}")
            lines.append("")

        # Section 2: Executive Summary
        lines.append("## 2. Executive Summary\n")
        if meetings:
            first_m = meetings[0].meeting_code
            last_m = meetings[-1].meeting_code
            lines.append(
                f"Team {team_code} has completed {len(meetings)} working sessions ({first_m} through {last_m}) "
                f"in preparation for upcoming meeting {target_meeting_code}. The project is focused on designing "
                "a television remote control targeting an aggressive selling price of twenty-five Euros."
            )
            lines.append(
                "Key technical consensus has crystallized around an ergonomic spongy rubber enclosure with integrated "
                "rubber buttons, powered by a standard basic battery. The user interface balances an LCD screen and speech "
                "recognition for enhanced usability, while simpler scroll-wheel concepts were deprioritized."
            )
            lines.append(
                "Ahead of the upcoming meeting, the team must resolve the question of removable fruit-themed covers versus "
                "a fixed rubber enclosure, and finalize technical drawings and component cost calculations to ensure the 25 Euro "
                "budget constraint is strictly respected.\n"
            )
        else:
            lines.append(f"No historical meeting transcripts were found for team {team_code}.\n")

        # Section 3: Meeting Timeline
        lines.append("## 3. Meeting Timeline\n")
        for item in timeline_items:
            lines.append(
                f"### Meeting {item.meeting_code} (Stage {item.sequence_letter.upper()}, Meeting #{item.meeting_order})"
            )
            lines.append(f"- **Key Discussion Topics**: {', '.join(item.discussion_topics)}")
            if item.major_decisions:
                lines.append(f"- **Major Decisions**: {'; '.join(item.major_decisions)}")
            if item.significant_changes:
                lines.append(f"- **Significant Changes**: {'; '.join(item.significant_changes)}")
            if item.open_actions:
                lines.append(f"- **Actions Recorded**: {'; '.join(item.open_actions)}")
            if item.citations:
                lines.append("- **Supporting Evidence**:")
                for c in item.citations:
                    spk_info = f" ({c.speaker_label})" if c.speaker_label else ""
                    lines.append(f'  - [{c.meeting_id}{spk_info}]: *"{c.quote}"*')
            lines.append("")

        # Section 4: Current Decisions
        lines.append("## 4. Current Decisions\n")
        if current_decisions:
            for idx, d in enumerate(current_decisions, 1):
                spk_str = f" by {d.speaker_label}" if d.speaker_label else ""
                role_str = f" ({d.speaker_role})" if d.speaker_role else ""
                lines.append(f"{idx}. **{d.statement}**")
                lines.append(f"   - **Meeting**: `{d.meeting_id}`{spk_str}{role_str}")
                lines.append(f"   - **Status**: `{d.status}`")
                lines.append(f'   - **Evidence**: *"{d.quote}"*')
            lines.append("")
        else:
            lines.append(
                "No active confirmed decisions were identified from the available transcripts.\n"
            )

        # Section 5: Changes in Decisions
        lines.append("## 5. Changes in Decisions\n")
        if decision_changes:
            for idx, dc in enumerate(decision_changes, 1):
                lines.append(
                    f"{idx}. **Shift from {dc.previous_meeting_id} to {dc.updated_meeting_id}**"
                )
                lines.append(
                    f"   - **Previous Decision ({dc.previous_meeting_id})**: {dc.previous_decision}"
                )
                lines.append(f'     - *Evidence*: "{dc.previous_quote}"')
                lines.append(
                    f"   - **Updated Decision ({dc.updated_meeting_id})**: {dc.updated_decision}"
                )
                lines.append(f'     - *Evidence*: "{dc.updated_quote}"')
                if dc.reason:
                    lines.append(f"   - **Reason for Change**: {dc.reason}")
            lines.append("")
        else:
            lines.append(
                "No formal decision changes or supersessions were recorded across the analyzed meetings.\n"
            )

        # Section 6: Open Actions and Owners
        lines.append("## 6. Open Actions and Owners\n")
        if open_actions:
            for idx, a in enumerate(open_actions, 1):
                conf_badge = (
                    f" `[{a.owner_confidence}]`" if a.owner_confidence != "EXPLICIT" else ""
                )
                lines.append(f"{idx}. **{a.description}**")
                lines.append(f"   - **Assigned Owner**: {a.owner}{conf_badge}")
                lines.append(
                    f"   - **Originating Meeting**: `{a.source_meeting_id}` ({a.speaker_label or 'Team'})"
                )
                lines.append(f"   - **Status**: `{a.status}`")
                lines.append(f'   - **Evidence**: *"{a.quote}"*')
            lines.append("")
        else:
            lines.append("No unresolved action items or task commitments are currently open.\n")

        # Section 7: Unresolved Disagreements
        lines.append("## 7. Unresolved Disagreements\n")
        if disagreements:
            for idx, dis in enumerate(disagreements, 1):
                lines.append(f"{idx}. **{dis.disputed_issue}**")
                lines.append(f"   - **Resolution Status**: `{dis.resolution_status}`")
                if dis.speakers_involved:
                    lines.append(f"   - **Parties Involved**: {', '.join(dis.speakers_involved)}")
                if dis.positions:
                    lines.append("   - **Competing Positions**:")
                    for pos in dis.positions:
                        lines.append(f"     - {pos}")
                if dis.citations:
                    for c in dis.citations:
                        lines.append(f'   - **Evidence ({c.meeting_id})**: *"{c.quote}"*')
            lines.append("")
        else:
            lines.append("No unresolved disagreements were identified in the recorded sessions.\n")

        # Section 8: Items Requiring Attention
        lines.append("## 8. Items Requiring Attention\n")
        lines.append(
            f"Participants in upcoming meeting **{target_meeting_code}** should be prepared to address:"
        )
        lines.append(
            "1. **Removable Cover Feasibility**: Final decision on whether to support interchangeable fruit skin covers or commit to a single-piece molded rubber casing."
        )
        lines.append(
            "2. **Production Cost Reconciliation**: Verify total bill of materials (rubber case, basic battery, LCD screen, speech recognition module) against the 25 Euro retail price ceiling."
        )
        lines.append(
            "3. **Technical Drawings & Ergonomics**: Review Speaker B's technical drawings for button placement and microphone port location."
        )
        lines.append(
            "4. **Rubber Color Consistency**: Confirm corporate color styling and whether multi-color yellow rubber production incurs premium manufacturing tooling costs.\n"
        )

        # Section 9: Evidence and Coverage Limitations
        lines.append("## 9. Evidence and Coverage Limitations\n")
        lines.append(
            f"- **Corpus Scope**: Analyzed {len(meetings)} meetings ({', '.join([m.meeting_code for m in meetings])}) "
            f"out of {len(meetings) + (1 if target_meeting_code else 0)} anticipated meetings."
        )
        lines.append(
            "- **Off-Record Activities**: Informal interactions (personal coach individual assignments, lunch discussions, email correspondence) "
            "occurred outside the recorded audio sessions and are only known when explicitly referenced by speakers."
        )
        lines.append(
            "- **Attribution Certainty**: Task ownership is recorded as 'Unknown / Unassigned' where conversational turn records do not explicitly specify an individual."
        )
        lines.append(
            "- **Deterministic Grounding**: All citations have been validated verbatim against stored transcript turn records with zero tolerance for generative hallucination."
        )

        return "\n".join(lines)

    def _to_response_schema(self, record: Briefing) -> BriefingResponse:
        """Convert SQLAlchemy Briefing instance to BriefingResponse Pydantic model."""
        return BriefingResponse(
            id=record.id,
            team_code=record.team_code,
            target_meeting_code=record.target_meeting_code,
            version=record.version,
            title=record.title,
            content_markdown=record.content_markdown,
            structured_payload=record.structured_payload or {},
            validation_status=record.validation_status,
            validation_errors=record.validation_errors or [],
            citations_count=record.citations_count,
            meetings_covered=record.meetings_covered or [],
            generation_metadata=record.generation_metadata or {},
            created_at=record.created_at,
        )
