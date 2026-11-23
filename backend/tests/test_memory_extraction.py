import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.models.memory import Memory
from app.services.llm_client import MockLLMClient
from app.services.memory_extraction_service import MemoryExtractionService


@pytest.fixture
def mock_team_data(db_session: Session):
    team = Team(id=uuid.uuid4(), team_code="TS3006")
    db_session.add(team)
    db_session.flush()

    meeting = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3006a",
        meeting_number=1,
        sequence_letter="a",
        source_filename="TS3006a.txt",
        source_sha256="sha123",
        raw_text="Full text",
    )
    db_session.add(meeting)
    db_session.flush()

    speaker = Speaker(
        id=uuid.uuid4(),
        meeting_id=meeting.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    db_session.add(speaker)
    db_session.flush()

    turn1 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=meeting.id,
        speaker_id=speaker.id,
        turn_index=0,
        start_time_str="00:00:10",
        start_time_seconds=10,
        raw_text="We have agreed to select the titanium material for our remote casing.",
        normalized_text="we have agreed to select the titanium material for our remote casing",
        speaker=speaker,
    )
    turn2 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=meeting.id,
        speaker_id=speaker.id,
        turn_index=1,
        start_time_str="00:00:30",
        start_time_seconds=30,
        raw_text="Speaker A will contact the industrial design firm by tomorrow morning.",
        normalized_text="speaker a will contact the industrial design firm by tomorrow morning",
        speaker=speaker,
    )
    db_session.add_all([turn1, turn2])
    db_session.flush()

    return {"team": team, "meeting": meeting, "speaker": speaker, "turns": [turn1, turn2]}


class MockEmbeddingService:
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.05] * 384 for _ in texts]


def test_extraction_success_and_validation(db_session: Session, mock_team_data):
    """Test standard extraction workflow with valid verbatim quotes."""
    mock_llm = MockLLMClient(
        canned_response={
            "memories": [
                {
                    "memory_type": "DECISION",
                    "statement": "The team selected titanium for the casing.",
                    "quote": "agreed to select the titanium material for our remote",
                    "speaker_label": "Speaker A",
                    "turn_index": 0,
                    "confidence": 0.95,
                    "metadata": {"topic": "case_material"},
                },
                {
                    "memory_type": "ACTION",
                    "statement": "Speaker A will contact the design firm.",
                    "quote": "Speaker A will contact the industrial design firm by tomorrow",
                    "speaker_label": "Speaker A",
                    "turn_index": 1,
                    "confidence": 0.90,
                    "metadata": {"topic": "vendor_contact", "owner": "Speaker A"},
                },
            ]
        }
    )

    service = MemoryExtractionService(
        db=db_session,
        llm_client=mock_llm,
        embedding_service=MockEmbeddingService(),
    )
    run = service.extract_memories_for_meeting(mock_team_data["meeting"].id)

    assert run.status == "COMPLETED"
    assert run.total_memories_extracted == 2
    assert run.total_memories_validated == 2
    assert run.total_memories_rejected == 0

    memories = (
        db_session.query(Memory).filter(Memory.meeting_id == mock_team_data["meeting"].id).all()
    )
    assert len(memories) == 2
    assert {m.memory_type for m in memories} == {"DECISION", "ACTION"}


def test_extraction_rejects_fabricated_quotes(db_session: Session, mock_team_data):
    """Test that candidate memories with fabricated or modified quotes are strictly rejected."""
    mock_llm = MockLLMClient(
        canned_response={
            "memories": [
                {
                    "memory_type": "DECISION",
                    "statement": "Fabricated memory",
                    "quote": "This sentence was never said anywhere in the meeting ever.",
                    "speaker_label": "Speaker A",
                    "turn_index": 0,
                    "confidence": 0.95,
                    "metadata": {"topic": "fake"},
                }
            ]
        }
    )

    service = MemoryExtractionService(
        db=db_session,
        llm_client=mock_llm,
        embedding_service=MockEmbeddingService(),
    )
    run = service.extract_memories_for_meeting(mock_team_data["meeting"].id)

    assert run.status == "COMPLETED"
    assert run.total_memories_extracted == 1
    assert run.total_memories_validated == 0
    assert run.total_memories_rejected == 1
    assert len(run.errors_json) == 1
    assert "not found verbatim" in run.errors_json[0]["reason"]

    # Verify no memory was persisted
    memories = (
        db_session.query(Memory).filter(Memory.meeting_id == mock_team_data["meeting"].id).all()
    )
    assert len(memories) == 0


def test_extraction_idempotency(db_session: Session, mock_team_data):
    """Running extraction again without force=True skips without re-processing."""
    mock_llm = MockLLMClient(
        canned_response={
            "memories": [
                {
                    "memory_type": "DECISION",
                    "statement": "The team selected titanium for the casing.",
                    "quote": "agreed to select the titanium material for our remote",
                    "speaker_label": "Speaker A",
                    "turn_index": 0,
                    "confidence": 0.95,
                    "metadata": {"topic": "case_material"},
                }
            ]
        }
    )

    service = MemoryExtractionService(
        db=db_session,
        llm_client=mock_llm,
        embedding_service=MockEmbeddingService(),
    )
    meeting_id = mock_team_data["meeting"].id
    run1 = service.extract_memories_for_meeting(meeting_id)
    assert run1.total_memories_validated == 1

    # Second run without force should return existing completed run
    run2 = service.extract_memories_for_meeting(meeting_id, force=False)
    assert run2.id == run1.id

    # Count of memories should remain 1
    memories = db_session.query(Memory).filter(Memory.meeting_id == meeting_id).all()
    assert len(memories) == 1
