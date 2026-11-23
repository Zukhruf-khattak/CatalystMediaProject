import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.dataset import Meeting, Team
from app.models.memory import Memory, MemoryRelationship, MemoryStatus, MemoryType, RelationshipType
from app.schemas.memory import MemorySearchFilter
from app.services.memory_retrieval_service import MemoryRetrievalService


@pytest.fixture
def populated_memories(db_session: Session):
    team1 = Team(id=uuid.uuid4(), team_code="TS3006")
    team2 = Team(id=uuid.uuid4(), team_code="TS3007")
    db_session.add_all([team1, team2])
    db_session.flush()

    m1 = Meeting(
        id=uuid.uuid4(),
        team_id=team1.id,
        meeting_code="TS3006a",
        meeting_number=1,
        sequence_letter="a",
        source_filename="TS3006a.txt",
        source_sha256="hash1",
        raw_text="text1",
    )
    m2 = Meeting(
        id=uuid.uuid4(),
        team_id=team1.id,
        meeting_code="TS3006c",
        meeting_number=3,
        sequence_letter="c",
        source_filename="TS3006c.txt",
        source_sha256="hash2",
        raw_text="text2",
    )
    m3 = Meeting(
        id=uuid.uuid4(),
        team_id=team2.id,
        meeting_code="TS3007a",
        meeting_number=1,
        sequence_letter="a",
        source_filename="TS3007a.txt",
        source_sha256="hash3",
        raw_text="text3",
    )
    db_session.add_all([m1, m2, m3])
    db_session.flush()

    mem1 = Memory(
        id=uuid.uuid4(),
        team_id=team1.id,
        meeting_id=m1.id,
        memory_type=MemoryType.DECISION.value,
        statement="Decided on titanium casing.",
        quote="We will definitely use titanium casing.",
        speaker_label="Speaker A",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.SUPERSEDED.value,
        confidence=0.9,
    )
    mem2 = Memory(
        id=uuid.uuid4(),
        team_id=team1.id,
        meeting_id=m2.id,
        memory_type=MemoryType.DECISION.value,
        statement="Decided to change case to rubber.",
        quote="We decided to change the casing to rubber.",
        speaker_label="Speaker B",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.CURRENT.value,
        confidence=0.95,
    )
    mem3 = Memory(
        id=uuid.uuid4(),
        team_id=team2.id,
        meeting_id=m3.id,
        memory_type=MemoryType.ACTION.value,
        statement="Alice will review power specs.",
        quote="Alice will review power specs tomorrow.",
        speaker_label="Speaker A",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.OPEN.value,
        confidence=0.85,
    )
    db_session.add_all([mem1, mem2, mem3])
    db_session.flush()

    rel = MemoryRelationship(
        id=uuid.uuid4(),
        source_memory_id=mem2.id,
        target_memory_id=mem1.id,
        relationship_type=RelationshipType.SUPERSEDES.value,
        rationale="Rubber supersedes titanium.",
        confidence=1.0,
    )
    db_session.add(rel)
    db_session.commit()

    return {"team1": team1, "team2": team2, "mem1": mem1, "mem2": mem2, "mem3": mem3}


def test_search_by_team(db_session: Session, populated_memories):
    service = MemoryRetrievalService(db=db_session)
    filters = MemorySearchFilter(team_code="TS3006")
    items, total = service.search_memories(filters)

    assert total == 2
    assert len(items) == 2
    assert all(i.team_id == populated_memories["team1"].id for i in items)


def test_search_by_type_and_status(db_session: Session, populated_memories):
    service = MemoryRetrievalService(db=db_session)
    filters = MemorySearchFilter(memory_type="DECISION", status="current")
    items, total = service.search_memories(filters)

    assert total == 1
    assert items[0].id == populated_memories["mem2"].id


def test_search_by_query_text(db_session: Session, populated_memories):
    service = MemoryRetrievalService(db=db_session)
    filters = MemorySearchFilter(query_text="rubber")
    items, total = service.search_memories(filters)

    assert total == 1
    assert items[0].id == populated_memories["mem2"].id


def test_get_memory_by_id_with_relationships(db_session: Session, populated_memories):
    service = MemoryRetrievalService(db=db_session)
    mem2 = service.get_memory_by_id(populated_memories["mem2"].id)

    assert mem2 is not None
    assert len(mem2.outgoing_relationships) == 1
    assert mem2.outgoing_relationships[0].relationship_type == RelationshipType.SUPERSEDES.value
    assert mem2.outgoing_relationships[0].target_memory_id == populated_memories["mem1"].id
