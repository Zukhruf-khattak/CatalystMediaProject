import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.dataset import Meeting, Team
from app.models.memory import (
    Memory,
    MemoryStatus,
    MemoryType,
    RelationshipType,
)
from app.services.temporal_reasoning import TemporalReasoningService


@pytest.fixture
def test_team(db_session: Session) -> Team:
    team = Team(id=uuid.uuid4(), team_code="TS3006")
    db_session.add(team)
    db_session.commit()
    return team


@pytest.fixture
def other_team(db_session: Session) -> Team:
    team = Team(id=uuid.uuid4(), team_code="TS3007")
    db_session.add(team)
    db_session.commit()
    return team


@pytest.fixture
def meetings(db_session: Session, test_team: Team) -> list[Meeting]:
    m1 = Meeting(
        id=uuid.uuid4(),
        team_id=test_team.id,
        meeting_code="TS3006a",
        meeting_number=1,
        sequence_letter="a",
        source_filename="TS3006a.txt",
        source_sha256="hash1",
        raw_text="text1",
    )
    m3 = Meeting(
        id=uuid.uuid4(),
        team_id=test_team.id,
        meeting_code="TS3006c",
        meeting_number=3,
        sequence_letter="c",
        source_filename="TS3006c.txt",
        source_sha256="hash3",
        raw_text="text3",
    )
    db_session.add_all([m1, m3])
    db_session.commit()
    return [m1, m3]


def test_decision_supersession(db_session: Session, test_team: Team, meetings: list[Meeting]):
    """Meeting A decides titanium case; Meeting C changes decision to curved rubber.

    Meeting A decision must remain in DB, marked 'superseded'.
    Meeting C decision becomes 'current'.
    A directed 'supersedes' edge connects C -> A.
    """
    service = TemporalReasoningService(db=db_session)

    # 1. Early decision in Meeting A
    dec_a = Memory(
        id=uuid.uuid4(),
        team_id=test_team.id,
        meeting_id=meetings[0].id,
        memory_type=MemoryType.DECISION.value,
        statement="The team decided to use a titanium case.",
        quote="We will go with the titanium case.",
        speaker_label="Speaker A",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.CURRENT.value,
        metadata_json={"topic": "case_material"},
    )
    db_session.add(dec_a)
    db_session.commit()

    # 2. Later decision in Meeting C
    dec_c = Memory(
        id=uuid.uuid4(),
        team_id=test_team.id,
        meeting_id=meetings[1].id,
        memory_type=MemoryType.DECISION.value,
        statement="The team decided to switch from titanium to curved rubber.",
        quote="Instead of titanium we will use curved rubber.",
        speaker_label="Speaker B",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.CURRENT.value,
        metadata_json={"topic": "case_material"},
    )
    db_session.add(dec_c)
    db_session.flush()

    rels = service.link_memory_to_prior_memories(new_memory=dec_c)

    assert len(rels) == 1
    rel = rels[0]
    assert rel.relationship_type == RelationshipType.SUPERSEDES.value
    assert rel.source_memory_id == dec_c.id
    assert rel.target_memory_id == dec_a.id
    assert rel.is_ambiguous is False

    # Historical decision preserved but status updated
    assert dec_a.status == MemoryStatus.SUPERSEDED.value
    assert dec_c.status == MemoryStatus.CURRENT.value


def test_ambiguous_relationship_leaves_status_unresolved(
    db_session: Session, test_team: Team, meetings: list[Meeting]
):
    """When a change is ambiguous, it is recorded with is_ambiguous=True without mutating status."""
    service = TemporalReasoningService(db=db_session)

    dec_a = Memory(
        id=uuid.uuid4(),
        team_id=test_team.id,
        meeting_id=meetings[0].id,
        memory_type=MemoryType.DECISION.value,
        statement="The team decided to use solar power.",
        quote="Let us try solar power for the batteries.",
        speaker_label="Speaker A",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.CURRENT.value,
        metadata_json={"topic": "power_source"},
    )
    db_session.add(dec_a)
    db_session.commit()

    dec_c = Memory(
        id=uuid.uuid4(),
        team_id=test_team.id,
        meeting_id=meetings[1].id,
        memory_type=MemoryType.DECISION.value,
        statement="Maybe we could reconsider regular batteries.",
        quote="Maybe regular batteries might be an alternative.",
        speaker_label="Speaker C",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.CURRENT.value,
        metadata_json={"topic": "power_source"},
    )
    db_session.add(dec_c)
    db_session.flush()

    rels = service.link_memory_to_prior_memories(new_memory=dec_c, is_ambiguous=True)

    assert len(rels) == 1
    assert rels[0].is_ambiguous is True
    # Earlier decision status remains CURRENT because change is ambiguous
    assert dec_a.status == MemoryStatus.CURRENT.value


def test_action_resolution(db_session: Session, test_team: Team, meetings: list[Meeting]):
    service = TemporalReasoningService(db=db_session)

    action_a = Memory(
        id=uuid.uuid4(),
        team_id=test_team.id,
        meeting_id=meetings[0].id,
        memory_type=MemoryType.ACTION.value,
        statement="Speaker B will check component supplier prices.",
        quote="Speaker B will check component supplier prices.",
        speaker_label="Speaker A",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.OPEN.value,
        metadata_json={"topic": "supplier_pricing", "owner": "Speaker B"},
    )
    db_session.add(action_a)
    db_session.commit()

    action_c = Memory(
        id=uuid.uuid4(),
        team_id=test_team.id,
        meeting_id=meetings[1].id,
        memory_type=MemoryType.ACTION.value,
        statement="Speaker B presented the supplier prices report.",
        quote="I have completed the supplier prices check.",
        speaker_label="Speaker B",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.CURRENT.value,
        metadata_json={"topic": "supplier_pricing"},
    )
    db_session.add(action_c)
    db_session.flush()

    rels = service.link_memory_to_prior_memories(
        new_memory=action_c,
        candidate_rel=RelationshipType.RESOLVES.value,
    )

    assert len(rels) == 1
    assert rels[0].relationship_type == RelationshipType.RESOLVES.value
    assert action_a.status == MemoryStatus.RESOLVED.value


def test_team_isolation(
    db_session: Session, test_team: Team, other_team: Team, meetings: list[Meeting]
):
    """Decisions from one team must never link to or supersede decisions of another team."""
    service = TemporalReasoningService(db=db_session)

    dec_team1 = Memory(
        id=uuid.uuid4(),
        team_id=test_team.id,
        meeting_id=meetings[0].id,
        memory_type=MemoryType.DECISION.value,
        statement="Team TS3006 decided on yellow casing.",
        quote="We decided on bright yellow for our case.",
        speaker_label="Speaker A",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.CURRENT.value,
        metadata_json={"topic": "case_color"},
    )
    db_session.add(dec_team1)
    db_session.commit()

    # Meeting for other team
    other_meeting = Meeting(
        id=uuid.uuid4(),
        team_id=other_team.id,
        meeting_code="TS3007a",
        meeting_number=1,
        sequence_letter="a",
        source_filename="TS3007a.txt",
        source_sha256="hash_other",
        raw_text="text_other",
    )
    db_session.add(other_meeting)
    db_session.commit()

    dec_team2 = Memory(
        id=uuid.uuid4(),
        team_id=other_team.id,
        meeting_id=other_meeting.id,
        memory_type=MemoryType.DECISION.value,
        statement="Team TS3007 decided on blue casing.",
        quote="We decided on dark blue for our case.",
        speaker_label="Speaker B",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.CURRENT.value,
        metadata_json={"topic": "case_color"},
    )
    db_session.add(dec_team2)
    db_session.flush()

    rels = service.link_memory_to_prior_memories(new_memory=dec_team2)

    # Must be 0 because different teams cannot link
    assert len(rels) == 0
    assert dec_team1.status == MemoryStatus.CURRENT.value
