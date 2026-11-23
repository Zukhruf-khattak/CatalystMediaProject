import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.dataset import IngestionJob, Meeting, Speaker, Team, TranscriptTurn
from app.schemas.dataset import IngestionJobCreate, IngestionJobResponse, IngestionStatsResponse
from app.services.archive_service import compute_sha256, validate_and_extract_archive
from app.services.embedding_service import get_embedding_service
from app.services.parser_service import parse_transcript_file

logger = get_logger("app.services.ingestion")


class IngestionError(AppException):
    """Raised when an unrecoverable ingestion failure occurs."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message=message, status_code=500, details=details or {})


def discover_transcript_files(dataset_dir: Path) -> List[Path]:
    """Find all transcript .txt files in dataset_dir, ignoring CREDITS.txt and non-meeting files."""
    if not dataset_dir.exists():
        return []

    discovered: List[Path] = []
    for file_path in sorted(dataset_dir.glob("*.txt")):
        if file_path.name.upper() == "CREDITS.TXT":
            continue
        discovered.append(file_path)

    # Also search subdirectories if transcripts were extracted into nested folders
    if not discovered:
        for file_path in sorted(dataset_dir.rglob("*.txt")):
            if file_path.name.upper() == "CREDITS.TXT":
                continue
            discovered.append(file_path)

    return discovered


class IngestionService:
    """Service to execute and monitor idempotent transcript ingestion."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.embedding_service = get_embedding_service()

    def get_stats(self) -> IngestionStatsResponse:
        """Calculate aggregate database statistics."""
        total_teams = self.db.scalar(select(func.count(Team.id))) or 0
        total_meetings = self.db.scalar(select(func.count(Meeting.id))) or 0
        total_speakers = self.db.scalar(select(func.count(Speaker.id))) or 0
        total_turns = self.db.scalar(select(func.count(TranscriptTurn.id))) or 0
        embedded_turns = (
            self.db.scalar(
                select(func.count(TranscriptTurn.id)).where(TranscriptTurn.embedding.is_not(None))
            )
            or 0
        )

        latest_job_record = self.db.execute(
            select(IngestionJob).order_by(IngestionJob.started_at.desc()).limit(1)
        ).scalar_one_or_none()

        latest_job = (
            IngestionJobResponse.model_validate(latest_job_record) if latest_job_record else None
        )

        return IngestionStatsResponse(
            total_teams=total_teams,
            total_meetings=total_meetings,
            total_speakers=total_speakers,
            total_turns=total_turns,
            embedded_turns=embedded_turns,
            latest_job=latest_job,
        )

    def get_job(self, job_id: uuid.UUID) -> Optional[IngestionJobResponse]:
        """Retrieve ingestion job status by ID."""
        job = self.db.get(IngestionJob, job_id)
        if not job:
            return None
        return IngestionJobResponse.model_validate(job)

    def list_jobs(self, limit: int = 50) -> List[IngestionJobResponse]:
        """List recent ingestion jobs."""
        records = (
            self.db.execute(
                select(IngestionJob).order_by(IngestionJob.started_at.desc()).limit(limit)
            )
            .scalars()
            .all()
        )
        return [IngestionJobResponse.model_validate(r) for r in records]

    def run_ingestion(
        self,
        options: Optional[IngestionJobCreate] = None,
        custom_dataset_dir: Optional[Path] = None,
    ) -> IngestionJobResponse:
        """Run batch ingestion job across discovered transcripts."""
        opts = options or IngestionJobCreate()
        dataset_path = custom_dataset_dir or Path(self.settings.dataset_dir)

        # 1. Check if raw transcripts exist, or if we need to safely extract from zip archive
        files = discover_transcript_files(dataset_path)
        archive_path = Path(self.settings.dataset_archive_path)

        if not files and archive_path.exists():
            logger.info(f"No text files found in {dataset_path}. Extracting from {archive_path}...")
            validate_and_extract_archive(
                archive_path=archive_path,
                destination_dir=dataset_path,
                max_size_bytes=self.settings.archive_max_size_bytes,
                max_files=self.settings.archive_max_extracted_files,
            )
            files = discover_transcript_files(dataset_path)

        if opts.limit_files and opts.limit_files > 0:
            files = files[: opts.limit_files]

        # 2. Create IngestionJob record
        job = IngestionJob(
            id=uuid.uuid4(),
            status="RUNNING",
            total_files=len(files),
            started_at=datetime.now(timezone.utc),
            errors_json=[],
            summary_json={
                "dataset_dir": str(dataset_path),
                "force_reingest": opts.force_reingest,
                "skip_embeddings": opts.skip_embeddings,
                "parser_version": self.settings.parser_version,
            },
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        start_time = time.perf_counter()
        logger.info(f"Starting Ingestion Job {job.id} for {len(files)} files...")

        completed = 0
        skipped = 0
        failed = 0
        total_turns = 0
        total_words = 0
        embedded_turns = 0
        errors: List[Dict[str, Any]] = []

        # 3. Process each transcript file with fault isolation
        for idx, file_path in enumerate(files):
            filename = file_path.name
            job.current_file = filename
            logger.info(f"[{idx + 1}/{len(files)}] Processing transcript: {filename}")

            try:
                # Compute SHA-256 for idempotency check
                sha256_hash = compute_sha256(file_path)

                # Check for existing meeting
                base_code = file_path.stem
                existing_meeting = self.db.execute(
                    select(Meeting).where(Meeting.meeting_code == base_code)
                ).scalar_one_or_none()

                if existing_meeting is not None:
                    if existing_meeting.source_sha256 == sha256_hash and not opts.force_reingest:
                        logger.info(
                            f"Meeting {base_code} already ingested with matching SHA-256. Skipping."
                        )
                        skipped += 1
                        job.skipped_meetings = skipped
                        self.db.commit()
                        continue
                    else:
                        logger.info(
                            f"Re-ingesting meeting {base_code} (force={opts.force_reingest})..."
                        )
                        self.db.delete(existing_meeting)
                        self.db.flush()

                # Parse transcript
                parsed = parse_transcript_file(file_path)

                # Process meeting in an isolated database transaction
                with self.db.begin_nested():
                    # 1. Upsert Team
                    team = self.db.execute(
                        select(Team).where(Team.team_code == parsed.team_code)
                    ).scalar_one_or_none()
                    if not team:
                        team = Team(team_code=parsed.team_code)
                        self.db.add(team)
                        self.db.flush()

                    # 2. Create Meeting
                    meeting = Meeting(
                        id=uuid.uuid4(),
                        team_id=team.id,
                        meeting_code=parsed.meeting_code,
                        meeting_number=parsed.meeting_number,
                        sequence_letter=parsed.sequence_letter,
                        total_turns=parsed.total_turns,
                        word_count=parsed.word_count,
                        duration_seconds=parsed.duration_seconds,
                        source_filename=parsed.source_filename,
                        source_sha256=parsed.source_sha256,
                        status="INGESTED",
                        raw_text=parsed.raw_text,
                        parser_version=self.settings.parser_version,
                    )
                    self.db.add(meeting)
                    self.db.flush()

                    # 3. Create Speakers (meeting-scoped)
                    speaker_map: Dict[str, Speaker] = {}
                    for spk in parsed.speakers:
                        speaker_record = Speaker(
                            id=uuid.uuid4(),
                            meeting_id=meeting.id,
                            speaker_label=spk.speaker_label,
                            speaker_letter=spk.speaker_letter,
                            role=spk.role,
                        )
                        self.db.add(speaker_record)
                        speaker_map[spk.speaker_label] = speaker_record
                    self.db.flush()

                    # 4. Generate Embeddings for turns if requested
                    embeddings: List[Optional[List[float]]] = [None] * len(parsed.turns)
                    if not opts.skip_embeddings:
                        turn_texts = [t.raw_text for t in parsed.turns]
                        generated = self.embedding_service.generate_embeddings(turn_texts)
                        embeddings = [g for g in generated]

                    # 5. Create Transcript Turns
                    for t_idx, turn_data in enumerate(parsed.turns):
                        # Find speaker or create on the fly if unseen in roster
                        speaker_obj = speaker_map.get(turn_data.speaker_label)
                        if not speaker_obj:
                            speaker_obj = Speaker(
                                id=uuid.uuid4(),
                                meeting_id=meeting.id,
                                speaker_label=turn_data.speaker_label,
                                speaker_letter=turn_data.speaker_letter,
                            )
                            self.db.add(speaker_obj)
                            self.db.flush()
                            speaker_map[turn_data.speaker_label] = speaker_obj

                        turn_record = TranscriptTurn(
                            id=uuid.uuid4(),
                            meeting_id=meeting.id,
                            speaker_id=speaker_obj.id,
                            turn_index=turn_data.turn_index,
                            start_time_str=turn_data.start_time_str,
                            start_time_seconds=turn_data.start_time_seconds,
                            end_time_seconds=turn_data.end_time_seconds,
                            raw_text=turn_data.raw_text,
                            normalized_text=turn_data.normalized_text,
                            embedding=embeddings[t_idx],
                        )
                        self.db.add(turn_record)

                # Commit completed meeting transaction
                self.db.commit()

                completed += 1
                total_turns += parsed.total_turns
                total_words += parsed.word_count
                if not opts.skip_embeddings:
                    embedded_turns += parsed.total_turns

                # Update running job record
                job.completed_meetings = completed
                job.total_turns = total_turns
                job.total_words = total_words
                job.embedded_turns = embedded_turns
                self.db.commit()

            except Exception as e:
                failed += 1
                logger.error(f"Failed to ingest transcript '{filename}': {e}")
                errors.append(
                    {
                        "filename": filename,
                        "error": str(e),
                        "trace": traceback.format_exc(limit=3),
                    }
                )
                job.failed_meetings = failed
                job.errors_json = list(errors)
                self.db.commit()
                self.db.commit()

        # Finalize job status
        elapsed = time.perf_counter() - start_time
        job.completed_at = datetime.now(timezone.utc)
        job.current_file = None
        if failed > 0 and completed == 0:
            job.status = "FAILED"
        elif failed > 0:
            job.status = "PARTIAL"
        else:
            job.status = "COMPLETED"

        job.summary_json = {
            **job.summary_json,
            "elapsed_seconds": round(elapsed, 2),
            "total_files": len(files),
            "completed_meetings": completed,
            "skipped_meetings": skipped,
            "failed_meetings": failed,
            "total_turns": total_turns,
            "total_words": total_words,
            "embedded_turns": embedded_turns,
        }
        self.db.commit()
        self.db.refresh(job)

        logger.info(
            f"Ingestion Job {job.id} completed with status '{job.status}' in {elapsed:.2f}s "
            f"[Completed: {completed}, Skipped: {skipped}, Failed: {failed}, Turns: {total_turns}]"
        )
        return IngestionJobResponse.model_validate(job)
