import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.dataset import Meeting, Team
from app.models.memory import (
    Memory,
    MemoryRelationship,
    MemoryStatus,
    MemoryType,
    RelationshipType,
)
from app.schemas.retrieval import RetrievalRequest
from app.services.hybrid_retrieval_service import HybridRetrievalService


@pytest.fixture
def temporal_dataset(db_session: Session):
    team = Team(id=uuid.uuid4(), team_code="TS3006")
    db_session.add(team)
    db_session.flush()

    m1 = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="ts3006a",
        meeting_number=1,
        sequence_letter="a",
        source_filename="TS3006a.txt",
        source_sha256="sha1",
        raw_text="Meeting a text",
    )
    m3 = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="ts3006c",
        meeting_number=3,
        sequence_letter="c",
        source_filename="TS3006c.txt",
        source_sha256="sha3",
        raw_text="Meeting c text",
    )
    db_session.add_all([m1, m3])
    db_session.flush()

    # Historical decision in Meeting A: titanium
    dec_a = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m1.id,
        memory_type=MemoryType.DECISION.value,
        statement="Team decided to use a titanium case.",
        quote="We will go with the titanium case.",
        speaker_label="Speaker A",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.SUPERSEDED.value,
        metadata_json={"topic": "case_material"},
    )
    # Current decision in Meeting C: rubber
    dec_c = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m3.id,
        memory_type=MemoryType.DECISION.value,
        statement="Team decided to switch to rubber casing.",
        quote="We decided to change to rubber.",
        speaker_label="Speaker B",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.CURRENT.value,
        metadata_json={"topic": "case_material"},
    )
    # Open disagreement in Meeting C: LCD screen vs simple buttons
    disag = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m3.id,
        memory_type=MemoryType.DISAGREEMENT.value,
        statement="Dispute over whether an LCD display is required.",
        quote="I strongly disagree that we need an LCD.",
        speaker_label="Speaker C",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.OPEN.value,
        metadata_json={"topic": "lcd_screen"},
    )
    db_session.add_all([dec_a, dec_c, disag])
    db_session.flush()

    # Link superseding relationship: dec_c supersedes dec_a
    rel = MemoryRelationship(
        id=uuid.uuid4(),
        source_memory_id=dec_c.id,
        target_memory_id=dec_a.id,
        relationship_type=RelationshipType.SUPERSEDES.value,
        rationale="Rubber supersedes titanium due to cost.",
        is_ambiguous=False,
    )
    db_session.add(rel)
    db_session.commit()

    return {"team": team, "m1": m1, "m3": m3, "dec_a": dec_a, "dec_c": dec_c, "disag": disag}


class MockEmbeddingService:
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.05] * 384 for _ in texts]


def test_retrieval_surfaces_current_and_superseded_memories(db_session: Session, temporal_dataset):
    service = HybridRetrievalService(db=db_session, embedding_service=MockEmbeddingService())
    req = RetrievalRequest(
        query="case material",
        team_code="TS3006",
        method="hybrid",
        include_temporal_memories=True,
    )
    pack = service.execute_retrieval(req)

    mem_ids = {m.memory_id for m in pack.temporal_memories}
    # Both current and superseded decisions must be included to trace temporal change
    assert temporal_dataset["dec_c"].id in mem_ids
    assert temporal_dataset["dec_a"].id in mem_ids

    # Verify that current decision comes first
    assert pack.temporal_memories[0].status == "current"

    # Verify relationship links are populated
    cur_mem = next(m for m in pack.temporal_memories if m.memory_id == temporal_dataset["dec_c"].id)
    assert len(cur_mem.outgoing_relationships) == 1
    assert cur_mem.outgoing_relationships[0].relationship_type == "supersedes"
    assert cur_mem.outgoing_relationships[0].target_memory_id == temporal_dataset["dec_a"].id


def test_retrieval_surfaces_unresolved_disagreements_separately(
    db_session: Session, temporal_dataset
):
    service = HybridRetrievalService(db=db_session, embedding_service=MockEmbeddingService())
    req = RetrievalRequest(
        query="lcd screen",
        team_code="TS3006",
        method="hybrid",
        include_temporal_memories=True,
    )
    pack = service.execute_retrieval(req)

    assert len(pack.unresolved_disagreements) >= 1
    dis = pack.unresolved_disagreements[0]
    assert dis.memory_id == temporal_dataset["disag"].id
    assert dis.status == "open"
    assert "LCD" in dis.quote
