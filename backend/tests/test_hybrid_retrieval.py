import json
import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.schemas.retrieval import RetrievalFilter, RetrievalRequest
from app.services.hybrid_retrieval_service import HybridRetrievalService


class ControlledMockEmbeddingService:
    """Mock embedding service returning predictable vectors for similarity testing."""

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        # Vector A (titanium topic): high on index 0
        # Vector B (rubber topic): high on index 1
        # Vector C (other topic): high on index 2
        results = []
        for t in texts:
            t_low = t.lower()
            if "titanium" in t_low:
                vec = [0.9, 0.1, 0.0] + [0.0] * 381
            elif "rubber" in t_low:
                vec = [0.1, 0.9, 0.0] + [0.0] * 381
            else:
                vec = [0.0, 0.1, 0.9] + [0.0] * 381
            results.append(vec)
        return results


@pytest.fixture
def hybrid_dataset(db_session: Session):
    team_a = Team(id=uuid.uuid4(), team_code="TS3006")
    team_b = Team(id=uuid.uuid4(), team_code="TS3007")
    db_session.add_all([team_a, team_b])
    db_session.flush()

    m1 = Meeting(
        id=uuid.uuid4(),
        team_id=team_a.id,
        meeting_code="ts3006a",
        meeting_number=1,
        sequence_letter="a",
        source_filename="TS3006a.txt",
        source_sha256="sha1",
        raw_text="Meeting 1 text",
    )
    m2 = Meeting(
        id=uuid.uuid4(),
        team_id=team_a.id,
        meeting_code="ts3006c",
        meeting_number=3,
        sequence_letter="c",
        source_filename="TS3006c.txt",
        source_sha256="sha2",
        raw_text="Meeting 3 text",
    )
    m_other = Meeting(
        id=uuid.uuid4(),
        team_id=team_b.id,
        meeting_code="ts3007a",
        meeting_number=1,
        sequence_letter="a",
        source_filename="TS3007a.txt",
        source_sha256="sha3",
        raw_text="Other team text",
    )
    db_session.add_all([m1, m2, m_other])
    db_session.flush()

    spk1 = Speaker(
        id=uuid.uuid4(),
        meeting_id=m1.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    spk2 = Speaker(
        id=uuid.uuid4(),
        meeting_id=m2.id,
        speaker_label="Speaker B",
        speaker_letter="B",
        role="Industrial Designer",
    )
    spk_other = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_other.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    db_session.add_all([spk1, spk2, spk_other])
    db_session.flush()

    # Turn 1 in Meeting A: proposes titanium
    t1 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m1.id,
        speaker_id=spk1.id,
        turn_index=1,
        start_time_str="00:01:00",
        start_time_seconds=60,
        raw_text="We have decided to use titanium material for our remote case.",
        normalized_text="we have decided to use titanium material for our remote case",
        embedding=json.dumps([0.9, 0.1, 0.0] + [0.0] * 381),
        speaker=spk1,
    )
    # Turn 2 in Meeting C: switches to rubber
    t2 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m2.id,
        speaker_id=spk2.id,
        turn_index=5,
        start_time_str="00:05:00",
        start_time_seconds=300,
        raw_text="Due to cost constraints we are switching from titanium to rubber.",
        normalized_text="due to cost constraints we are switching from titanium to rubber",
        embedding=json.dumps([0.1, 0.9, 0.0] + [0.0] * 381),
        speaker=spk2,
    )
    # Turn in other team: mentions titanium but belongs to TS3007
    t_other = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_other.id,
        speaker_id=spk_other.id,
        turn_index=1,
        start_time_str="00:01:00",
        start_time_seconds=60,
        raw_text="Team TS3007 also looked at titanium casings.",
        normalized_text="team ts3007 also looked at titanium casings",
        embedding=json.dumps([0.9, 0.1, 0.0] + [0.0] * 381),
        speaker=spk_other,
    )
    db_session.add_all([t1, t2, t_other])
    db_session.flush()

    return {
        "team_a": team_a,
        "team_b": team_b,
        "m1": m1,
        "m2": m2,
        "m_other": m_other,
        "t1": t1,
        "t2": t2,
        "t_other": t_other,
    }


def test_keyword_search_channel(db_session: Session, hybrid_dataset):
    service = HybridRetrievalService(db=db_session)
    filters = RetrievalFilter(team_code="TS3006")
    results = service.search_turns_keyword("titanium material", filters=filters)

    assert len(results) >= 1
    # First match should be t1 (matches both 'titanium' and 'material')
    top_turn, score = results[0]
    assert top_turn.id == hybrid_dataset["t1"].id
    assert score > 0.0


def test_vector_search_channel(db_session: Session, hybrid_dataset):
    mock_emb = ControlledMockEmbeddingService()
    service = HybridRetrievalService(db=db_session, embedding_service=mock_emb)
    filters = RetrievalFilter(team_code="TS3006")

    # Query for rubber
    results = service.search_turns_vector("rubber casing options", filters=filters)

    assert len(results) >= 1
    # Top result should be t2 (high cosine similarity with rubber vector)
    top_turn, score = results[0]
    assert top_turn.id == hybrid_dataset["t2"].id
    assert score > 0.7


def test_hybrid_rrf_combines_channels(db_session: Session, hybrid_dataset):
    mock_emb = ControlledMockEmbeddingService()
    service = HybridRetrievalService(db=db_session, embedding_service=mock_emb)

    req = RetrievalRequest(
        query="Team TS3006 switched from titanium to rubber",
        method="hybrid",
        limit=5,
    )
    pack = service.execute_retrieval(req)

    assert pack.total_results >= 2
    turn_ids = {t.turn_id for t in pack.transcript_segments}
    assert hybrid_dataset["t1"].id in turn_ids
    assert hybrid_dataset["t2"].id in turn_ids

    # Both turns have valid scores
    for item in pack.transcript_segments:
        assert item.score > 0.0


def test_multi_meeting_evidence_retrieval(db_session: Session, hybrid_dataset):
    mock_emb = ControlledMockEmbeddingService()
    service = HybridRetrievalService(db=db_session, embedding_service=mock_emb)

    req = RetrievalRequest(
        query="Team TS3006 planned titanium and then switched to rubber",
        method="hybrid",
        limit=5,
    )
    pack = service.execute_retrieval(req)

    # Multi-meeting breakdown contains both meeting 'a' and meeting 'c'
    assert "ts3006a" in pack.cross_meeting_summary
    assert "ts3006c" in pack.cross_meeting_summary
    assert len(pack.cross_meeting_summary) >= 2


def test_team_isolation(db_session: Session, hybrid_dataset):
    mock_emb = ControlledMockEmbeddingService()
    service = HybridRetrievalService(db=db_session, embedding_service=mock_emb)

    req = RetrievalRequest(
        query="titanium",
        team_code="TS3006",
        method="hybrid",
        limit=10,
    )
    pack = service.execute_retrieval(req)

    # Must NOT contain turn from other team TS3007
    retrieved_ids = [t.turn_id for t in pack.transcript_segments]
    assert hybrid_dataset["t_other"].id not in retrieved_ids
    assert all(t.meeting_code.startswith("ts3006") for t in pack.transcript_segments)


def test_empty_query_handling(db_session: Session, hybrid_dataset):
    service = HybridRetrievalService(db=db_session)
    req = RetrievalRequest(query="   ", method="hybrid")
    pack = service.execute_retrieval(req)

    assert pack.total_results == 0
    assert len(pack.transcript_segments) == 0
