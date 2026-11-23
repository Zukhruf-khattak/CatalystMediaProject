from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.schemas.dataset import IngestionJobCreate
from app.services.ingestion_service import IngestionService

SAMPLE_M1 = """Meeting: TS3001a
Team: TS3001
Meeting number: 1 (a) of the team's four meetings
Speakers: Speaker A, Speaker B

00:00:10 Speaker A
First meeting kickoff utterance.

00:00:20 Speaker B
Sounds good to me.
"""

SAMPLE_M2 = """Meeting: TS3001b
Team: TS3001
Meeting number: 2 (b) of the team's four meetings
Speakers: Speaker A, Speaker B

00:00:15 Speaker A
Second meeting discussion on materials.

00:00:30 Speaker B
Let us use rubber.
"""

SAMPLE_CORRUPT = """Meeting: BADMEETING

This file has no turns and invalid format.
"""


def test_ingestion_persistence_and_relationships(tmp_path: Path, db_session: Session) -> None:
    # Write sample meeting files
    (tmp_path / "TS3001a.txt").write_text(SAMPLE_M1, encoding="utf-8")

    service = IngestionService(db=db_session)
    job = service.run_ingestion(
        options=IngestionJobCreate(skip_embeddings=True),
        custom_dataset_dir=tmp_path,
    )

    assert job.status == "COMPLETED"
    assert job.completed_meetings == 1
    assert job.total_turns == 2

    # Query DB entities
    team = db_session.execute(select(Team).where(Team.team_code == "TS3001")).scalar_one()
    assert team.team_code == "TS3001"

    meeting = db_session.execute(
        select(Meeting).where(Meeting.meeting_code == "TS3001a")
    ).scalar_one()
    assert meeting.team_id == team.id
    assert meeting.meeting_number == 1
    assert meeting.sequence_letter == "a"
    assert meeting.total_turns == 2
    assert "First meeting kickoff utterance." in meeting.raw_text

    speakers = (
        db_session.execute(select(Speaker).where(Speaker.meeting_id == meeting.id)).scalars().all()
    )
    assert len(speakers) == 2
    assert {s.speaker_label for s in speakers} == {"Speaker A", "Speaker B"}

    turns = (
        db_session.execute(
            select(TranscriptTurn)
            .where(TranscriptTurn.meeting_id == meeting.id)
            .order_by(TranscriptTurn.turn_index)
        )
        .scalars()
        .all()
    )
    assert len(turns) == 2
    assert turns[0].turn_index == 0
    assert turns[0].raw_text == "First meeting kickoff utterance."
    assert turns[1].turn_index == 1
    assert turns[1].raw_text == "Sounds good to me."


def test_ingestion_idempotency(tmp_path: Path, db_session: Session) -> None:
    (tmp_path / "TS3001a.txt").write_text(SAMPLE_M1, encoding="utf-8")

    service = IngestionService(db=db_session)

    # First run
    job1 = service.run_ingestion(
        options=IngestionJobCreate(skip_embeddings=True),
        custom_dataset_dir=tmp_path,
    )
    assert job1.completed_meetings == 1
    assert job1.skipped_meetings == 0

    # Second run without force -> should skip
    job2 = service.run_ingestion(
        options=IngestionJobCreate(skip_embeddings=True, force_reingest=False),
        custom_dataset_dir=tmp_path,
    )
    assert job2.completed_meetings == 0
    assert job2.skipped_meetings == 1

    # Total meetings in DB should still be 1 (no duplicates)
    count = db_session.scalar(select(Meeting).where(Meeting.meeting_code == "TS3001a"))
    assert count is not None


def test_ingestion_force_reingest(tmp_path: Path, db_session: Session) -> None:
    (tmp_path / "TS3001a.txt").write_text(SAMPLE_M1, encoding="utf-8")

    service = IngestionService(db=db_session)
    service.run_ingestion(
        options=IngestionJobCreate(skip_embeddings=True), custom_dataset_dir=tmp_path
    )

    # Force re-ingestion
    job_force = service.run_ingestion(
        options=IngestionJobCreate(skip_embeddings=True, force_reingest=True),
        custom_dataset_dir=tmp_path,
    )
    assert job_force.completed_meetings == 1
    assert job_force.skipped_meetings == 0


def test_speaker_identity_is_meeting_scoped(tmp_path: Path, db_session: Session) -> None:
    (tmp_path / "TS3001a.txt").write_text(SAMPLE_M1, encoding="utf-8")
    (tmp_path / "TS3001b.txt").write_text(SAMPLE_M2, encoding="utf-8")

    service = IngestionService(db=db_session)
    service.run_ingestion(
        options=IngestionJobCreate(skip_embeddings=True), custom_dataset_dir=tmp_path
    )

    m1 = db_session.execute(select(Meeting).where(Meeting.meeting_code == "TS3001a")).scalar_one()
    m2 = db_session.execute(select(Meeting).where(Meeting.meeting_code == "TS3001b")).scalar_one()

    spk_a_m1 = db_session.execute(
        select(Speaker).where(Speaker.meeting_id == m1.id, Speaker.speaker_label == "Speaker A")
    ).scalar_one()

    spk_a_m2 = db_session.execute(
        select(Speaker).where(Speaker.meeting_id == m2.id, Speaker.speaker_label == "Speaker A")
    ).scalar_one()

    # Distinct speaker rows for distinct meetings
    assert spk_a_m1.id != spk_a_m2.id
    assert spk_a_m1.meeting_id == m1.id
    assert spk_a_m2.meeting_id == m2.id


def test_fault_isolation_one_bad_file_does_not_rollback_good_files(
    tmp_path: Path, db_session: Session
) -> None:
    (tmp_path / "TS3001a.txt").write_text(SAMPLE_M1, encoding="utf-8")
    (tmp_path / "CORRUPT.txt").write_text(SAMPLE_CORRUPT, encoding="utf-8")

    service = IngestionService(db=db_session)
    job = service.run_ingestion(
        options=IngestionJobCreate(skip_embeddings=True),
        custom_dataset_dir=tmp_path,
    )

    assert job.status == "PARTIAL"
    assert job.completed_meetings == 1
    assert job.failed_meetings == 1
    assert len(job.errors_json) == 1
    assert job.errors_json[0]["filename"] == "CORRUPT.txt"

    # Good meeting was still committed safely
    m1 = db_session.execute(
        select(Meeting).where(Meeting.meeting_code == "TS3001a")
    ).scalar_one_or_none()
    assert m1 is not None
