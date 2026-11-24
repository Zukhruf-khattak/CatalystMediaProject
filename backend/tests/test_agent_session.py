import uuid

import pytest
from sqlalchemy.orm import Session

from app.agent.service import AgentService
from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.schemas.agent import AgentQueryRequest
from app.services.llm_client import MockLLMClient


@pytest.fixture
def session_test_db(db_session: Session) -> Session:
    """Seed test data for session persistence tests."""
    team = Team(id=uuid.uuid4(), team_code="TS3006")
    m_a = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3006a",
        sequence_letter="a",
        meeting_number=1,
        source_filename="TS3006a.txt",
        source_sha256="sha_ts3006a",
        raw_text="Meeting TS3006a transcript text",
    )
    spk_a = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_a.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    turn = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_a.id,
        speaker_id=spk_a.id,
        turn_index=0,
        start_time_str="00:00:10",
        start_time_seconds=10,
        raw_text="We have a strict budget of twenty-five Euros for the entire unit.",
        normalized_text="we have a strict budget of twenty five euros for the entire unit",
    )
    db_session.add_all([team, m_a, spk_a, turn])
    db_session.commit()
    return db_session


def test_agent_session_persistence_and_multi_turn(session_test_db: Session) -> None:
    mock_llm = MockLLMClient(
        canned_response="In TS3006a, the project manager set the unit budget at twenty-five Euros."
    )
    service = AgentService(db=session_test_db, llm_client=mock_llm)
    session_id = str(uuid.uuid4())

    # Turn 1
    req1 = AgentQueryRequest(
        question="What was the budget for the remote control in TS3006?",
        team_code="TS3006",
        session_id=session_id,
    )
    res1 = service.query(req1)
    assert res1.session_id == session_id
    assert res1.is_sufficient is True

    # Inspect persisted session
    detail1 = service.get_session(session_id)
    assert detail1 is not None
    assert detail1.turn_count == 1
    assert len(detail1.history) == 1
    assert detail1.history[0]["question"] == req1.question

    # Turn 2: Follow-up question in the same session
    req2 = AgentQueryRequest(
        question="Who announced this budget constraint?",
        team_code="TS3006",
        session_id=session_id,
    )
    res2 = service.query(req2)
    assert res2.session_id == session_id

    # Verify session history updated to 2 turns
    detail2 = service.get_session(session_id)
    assert detail2 is not None
    assert detail2.turn_count == 2
    assert len(detail2.history) == 2
    assert detail2.history[1]["question"] == req2.question


def test_agent_session_not_found(session_test_db: Session) -> None:
    service = AgentService(db=session_test_db)
    detail = service.get_session("non-existent-session-id-12345")
    assert detail is None


def test_agent_status_endpoint_data(session_test_db: Session) -> None:
    service = AgentService(db=session_test_db)
    status_obj = service.get_status()
    assert status_obj.status == "operational"
    assert "hybrid_search" in status_obj.tools_available
    assert "search_temporal_memory" in status_obj.tools_available
    assert "Memory" in status_obj.checkpointer
