import uuid

import pytest
from sqlalchemy.orm import Session

from app.agent.tools import AgentTools
from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.models.memory import Memory, MemoryRelationship, MemoryStatus, MemoryType, RelationshipType


@pytest.fixture
def seeded_tools_db(db_session: Session) -> Session:
    """Seed test data for tool execution tests."""
    team = Team(id=uuid.uuid4(), team_code="TS3006")
    db_session.add(team)

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
    m_b = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3006b",
        sequence_letter="b",
        meeting_number=2,
        source_filename="TS3006b.txt",
        source_sha256="sha_ts3006b",
        raw_text="Meeting TS3006b transcript text",
    )
    db_session.add_all([m_a, m_b])

    spk_a = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_a.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    spk_b = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_b.id,
        speaker_label="Speaker B",
        speaker_letter="B",
        role="Industrial Designer",
    )
    db_session.add_all([spk_a, spk_b])

    turn1 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_a.id,
        speaker_id=spk_a.id,
        turn_index=0,
        start_time_str="00:00:10",
        start_time_seconds=10,
        raw_text="Let us consider incorporating fruit and vegetable shapes for the new remote.",
        normalized_text="let us consider incorporating fruit and vegetable shapes for the new remote",
    )
    turn2 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_b.id,
        speaker_id=spk_b.id,
        turn_index=1,
        start_time_str="00:00:25",
        start_time_seconds=25,
        raw_text="The fruit shapes are a bit childish and too expensive to mould so we drop them.",
        normalized_text="the fruit shapes are a bit childish and too expensive to mould so we drop them",
    )
    db_session.add_all([turn1, turn2])

    mem1 = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m_a.id,
        turn_id=turn1.id,
        memory_type=MemoryType.PREFERENCE.value,
        statement="The team considered using fruit and vegetable shapes for the remote.",
        quote="fruit and vegetable shapes for the new remote",
        speaker_label="Speaker A",
        speaker_role="Project Manager",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.SUPERSEDED.value,
    )
    mem2 = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m_b.id,
        turn_id=turn2.id,
        memory_type=MemoryType.DECISION.value,
        statement="The team dropped the fruit shapes because they were childish and expensive.",
        quote="fruit shapes are a bit childish and too expensive to mould",
        speaker_label="Speaker B",
        speaker_role="Industrial Designer",
        meeting_order=2,
        sequence_letter="b",
        status=MemoryStatus.CURRENT.value,
    )
    db_session.add_all([mem1, mem2])

    rel = MemoryRelationship(
        id=uuid.uuid4(),
        source_memory_id=mem2.id,
        target_memory_id=mem1.id,
        relationship_type=RelationshipType.SUPERSEDES.value,
        rationale="Meeting B dropped the earlier fruit shape concept due to cost.",
    )
    db_session.add(rel)
    db_session.commit()
    return db_session


def test_tool_hybrid_search(seeded_tools_db: Session) -> None:
    tools = AgentTools(seeded_tools_db)
    res = tools.hybrid_search(query="fruit shapes childish", team_code="TS3006")
    assert "turns" in res
    assert len(res["turns"]) >= 1
    assert "childish and too expensive" in res["turns"][0]["text"]


def test_tool_search_temporal_memory(seeded_tools_db: Session) -> None:
    tools = AgentTools(seeded_tools_db)
    memories = tools.search_temporal_memory(
        query="fruit",
        team_code="TS3006",
        memory_type="DECISION",
        status="current",
    )
    assert len(memories) >= 1
    assert memories[0]["memory_type"] == "DECISION"
    assert memories[0]["status"] == "current"
    assert "childish" in memories[0]["statement"]


def test_tool_get_meeting_details(seeded_tools_db: Session) -> None:
    tools = AgentTools(seeded_tools_db)
    details = tools.get_meeting_details(meeting_code="TS3006a")
    assert details is not None
    assert details["meeting_code"] == "TS3006a"
    assert details["team_code"] == "TS3006"
    assert details["total_turns"] == 1
    assert len(details["speakers"]) == 1
    assert details["speakers"][0]["speaker_label"] == "Speaker A"


def test_tool_get_related_meetings(seeded_tools_db: Session) -> None:
    tools = AgentTools(seeded_tools_db)
    meetings = tools.get_related_meetings(team_code="TS3006")
    assert len(meetings) == 2
    assert meetings[0]["meeting_code"] == "TS3006a"
    assert meetings[1]["meeting_code"] == "TS3006b"
    assert meetings[0]["meeting_order"] == 1
    assert meetings[1]["meeting_order"] == 2


def test_tool_get_memory_history(seeded_tools_db: Session) -> None:
    tools = AgentTools(seeded_tools_db)
    # Search for mem2 to get its UUID
    mem2_list = tools.search_temporal_memory(query="childish", team_code="TS3006")
    assert len(mem2_list) >= 1
    mem2_id = mem2_list[0]["memory_id"]

    history = tools.get_memory_history(memory_id=mem2_id)
    assert "history" in history
    assert len(history["history"]) == 2
    # Verify chronological sorting (order 1 then order 2)
    assert history["history"][0]["meeting_order"] == 1
    assert history["history"][1]["meeting_order"] == 2


def test_tool_execution_telemetry_and_unknown_tool(seeded_tools_db: Session) -> None:
    tools = AgentTools(seeded_tools_db)
    record = tools.execute_tool("unknown_tool_xyz", param="test")
    assert record["error"] is not None
    assert "Unknown tool" in record["error"]

    valid_record = tools.execute_tool("get_related_meetings", team_code="TS3006")
    assert valid_record["error"] is None
    assert valid_record["duration_ms"] >= 0.0
    assert len(valid_record["result"]) == 2
