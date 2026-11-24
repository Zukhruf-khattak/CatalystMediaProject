"""Comprehensive test suite for Phase 7: Team TS3012 Pre-Meeting Briefing."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.dataset import Meeting, Speaker, Team, TranscriptTurn
from app.models.memory import (
    Memory,
    MemoryRelationship,
    MemoryStatus,
    MemoryType,
    RelationshipType,
)
from app.services.briefing_service import BriefingService
from app.services.citation_validation_service import CitationValidationService


@pytest.fixture
def ts3012_test_db(db_session: Session) -> Session:
    """
    Seed structured test fixture for Team TS3012 across meetings a, b, c, and d.
    Includes speakers, realistic turns, memories, and supersession relationships.
    """
    team = Team(id=uuid.uuid4(), team_code="TS3012")

    # Meetings a, b, c, d
    m_a = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3012a",
        sequence_letter="a",
        meeting_number=1,
        source_filename="TS3012a.txt",
        source_sha256="sha_ts12a",
        raw_text="Meeting TS3012a transcript text",
    )
    m_b = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3012b",
        sequence_letter="b",
        meeting_number=2,
        source_filename="TS3012b.txt",
        source_sha256="sha_ts12b",
        raw_text="Meeting TS3012b transcript text",
    )
    m_c = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3012c",
        sequence_letter="c",
        meeting_number=3,
        source_filename="TS3012c.txt",
        source_sha256="sha_ts12c",
        raw_text="Meeting TS3012c transcript text",
    )
    m_d = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3012d",
        sequence_letter="d",
        meeting_number=4,
        source_filename="TS3012d.txt",
        source_sha256="sha_ts12d",
        raw_text="Meeting TS3012d transcript text",
    )

    # Speakers for TS3012a
    spk_a_pm = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_a.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    spk_a_ui = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_a.id,
        speaker_label="Speaker B",
        speaker_letter="B",
        role="User Interface Designer",
    )
    spk_a_id = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_a.id,
        speaker_label="Speaker C",
        speaker_letter="C",
        role="Industrial Designer",
    )
    spk_a_mkt = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_a.id,
        speaker_label="Speaker D",
        speaker_letter="D",
        role="Marketing Expert",
    )

    # Speakers for TS3012c
    spk_c_pm = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_c.id,
        speaker_label="Speaker A",
        speaker_letter="A",
        role="Project Manager",
    )
    spk_c_ui = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_c.id,
        speaker_label="Speaker B",
        speaker_letter="B",
        role="User Interface Designer",
    )
    spk_c_id = Speaker(
        id=uuid.uuid4(),
        meeting_id=m_c.id,
        speaker_label="Speaker C",
        speaker_letter="C",
        role="Industrial Designer",
    )

    # Turns
    # Meeting A: Selling price target
    turn_a1 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_a.id,
        speaker_id=spk_a_pm.id,
        turn_index=15,
        start_time_str="00:12:43",
        start_time_seconds=763,
        raw_text="What we are going to feature Selling price, twenty five Euros.",
        normalized_text="what we are going to feature selling price twenty five euros",
    )

    # Meeting B: Initial plastic casing lean
    turn_b1 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_b.id,
        speaker_id=spk_a_ui.id,
        turn_index=20,
        start_time_str="00:10:15",
        start_time_seconds=615,
        raw_text="I think we should definitely go for plastic because I have curves in my design.",
        normalized_text="i think we should definitely go for plastic because i have curves in my design",
    )

    # Meeting C: Switch to rubber casing
    turn_c1 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_c.id,
        speaker_id=spk_c_pm.id,
        turn_index=40,
        start_time_str="00:17:52",
        start_time_seconds=1072,
        raw_text="Okay, so we are definitely going for rubber for the outer casing.",
        normalized_text="okay so we are definitely going for rubber for the outer casing",
    )

    # Meeting C: Power source (basic battery)
    turn_c2 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_c.id,
        speaker_id=spk_c_id.id,
        turn_index=55,
        start_time_str="00:04:59",
        start_time_seconds=299,
        raw_text="This is really a really basic battery, a normal battery rather than kinetic provision.",
        normalized_text="this is really a really basic battery a normal battery rather than kinetic provision",
    )

    # Meeting C: Open action
    turn_c3 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_c.id,
        speaker_id=spk_c_pm.id,
        turn_index=90,
        start_time_str="00:37:41",
        start_time_seconds=2261,
        raw_text="You doodle a doodle us a nice nice design for the next meeting.",
        normalized_text="you doodle a doodle us a nice nice design for the next meeting",
    )

    # Meeting C: Unresolved disagreement (removable fruit cover)
    turn_c4 = TranscriptTurn(
        id=uuid.uuid4(),
        meeting_id=m_c.id,
        speaker_id=spk_c_pm.id,
        turn_index=98,
        start_time_str="00:39:16",
        start_time_seconds=2356,
        raw_text="But we do not use removable cover maybe later, maybe we can decide that.",
        normalized_text="but we do not use removable cover maybe later maybe we can decide that",
    )

    # Memories
    mem_price = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m_a.id,
        turn_id=turn_a1.id,
        memory_type=MemoryType.DECISION.value,
        statement="The team established a target selling price of twenty-five Euros.",
        quote="What we are going to feature Selling price, twenty five Euros.",
        speaker_label="Speaker A",
        speaker_role="Project Manager",
        meeting_order=1,
        sequence_letter="a",
        status=MemoryStatus.CURRENT.value,
    )

    mem_plastic = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m_b.id,
        turn_id=turn_b1.id,
        memory_type=MemoryType.DECISION.value,
        statement="The team initially favored plastic casing to accommodate curved styling.",
        quote="definitely go for plastic because I have curves in my design.",
        speaker_label="Speaker B",
        speaker_role="User Interface Designer",
        meeting_order=2,
        sequence_letter="b",
        status=MemoryStatus.SUPERSEDED.value,
    )

    mem_rubber = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m_c.id,
        turn_id=turn_c1.id,
        memory_type=MemoryType.DECISION.value,
        statement="The team decided on spongy rubber casing for drop durability and trendy feel.",
        quote="Okay, so we are definitely going for rubber for the outer casing.",
        speaker_label="Speaker A",
        speaker_role="Project Manager",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.CURRENT.value,
    )

    # Supersession relationship: Rubber supersedes Plastic
    rel_casing = MemoryRelationship(
        id=uuid.uuid4(),
        source_memory_id=mem_rubber.id,
        target_memory_id=mem_plastic.id,
        relationship_type=RelationshipType.SUPERSEDES.value,
        rationale="Market research from Paris showed trendiness of rubber and drop protection.",
    )

    mem_battery = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m_c.id,
        turn_id=turn_c2.id,
        memory_type=MemoryType.DECISION.value,
        statement="The device will use a standard basic battery instead of kinetic energy.",
        quote="really a really basic battery, a normal battery rather than kinetic",
        speaker_label="Speaker C",
        speaker_role="Industrial Designer",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.CURRENT.value,
    )

    mem_action = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m_c.id,
        turn_id=turn_c3.id,
        memory_type=MemoryType.ACTION.value,
        statement="Speaker B must prepare refined technical drawings for the next meeting.",
        quote="doodle a doodle us a nice nice design for the next meeting.",
        speaker_label="Speaker A",
        speaker_role="Project Manager",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.OPEN.value,
    )

    mem_dispute = Memory(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_id=m_c.id,
        turn_id=turn_c4.id,
        memory_type=MemoryType.DISAGREEMENT.value,
        statement="Whether to feature a removable fruit-themed cover or a fixed rubber case.",
        quote="use removable cover maybe later, maybe we can decide that.",
        speaker_label="Speaker A",
        speaker_role="Project Manager",
        meeting_order=3,
        sequence_letter="c",
        status=MemoryStatus.OPEN.value,
    )

    db_session.add_all(
        [
            team,
            m_a,
            m_b,
            m_c,
            m_d,
            spk_a_pm,
            spk_a_ui,
            spk_a_id,
            spk_a_mkt,
            spk_c_pm,
            spk_c_ui,
            spk_c_id,
            turn_a1,
            turn_b1,
            turn_c1,
            turn_c2,
            turn_c3,
            turn_c4,
            mem_price,
            mem_plastic,
            mem_rubber,
            rel_casing,
            mem_battery,
            mem_action,
            mem_dispute,
        ]
    )
    db_session.commit()
    return db_session


# -----------------------------------------------------------------------------
# 1. Meeting Filtering and Chronology
# -----------------------------------------------------------------------------
def test_ts3012_meeting_filtering_and_chronology(ts3012_test_db: Session) -> None:
    """Verify that meetings prior to target TS3012d are retrieved in ascending chronological order."""
    service = BriefingService(ts3012_test_db)
    meetings, target_m, all_m, missing = service._get_chronological_meetings("TS3012", "TS3012d")

    assert target_m is not None
    assert target_m.meeting_code == "TS3012d"
    assert len(meetings) == 3
    assert [m.meeting_code for m in meetings] == ["TS3012a", "TS3012b", "TS3012c"]
    assert missing == []


# -----------------------------------------------------------------------------
# 2. Current Decision Identification
# -----------------------------------------------------------------------------
def test_current_decision_identification(ts3012_test_db: Session) -> None:
    """Verify that latest decisions are identified as CURRENT with valid quotations."""
    service = BriefingService(ts3012_test_db)
    meetings, _, _, _ = service._get_chronological_meetings("TS3012", "TS3012d")
    current_decisions = service._extract_current_decisions("TS3012", meetings)

    statements = [d.statement for d in current_decisions]
    assert any("twenty-five Euros" in s for s in statements)
    assert any("rubber" in s for s in statements)
    assert any("basic battery" in s for s in statements)
    # The superseded plastic decision should not appear in current decisions
    assert not any("initially favored plastic" in s for s in statements)

    # All decisions must have >= 6 words quotation
    for d in current_decisions:
        assert len(d.quote.split()) >= 6
        assert d.status == "CURRENT"


# -----------------------------------------------------------------------------
# 3. Decision Supersession and Changes
# -----------------------------------------------------------------------------
def test_decision_supersession_and_changes(ts3012_test_db: Session) -> None:
    """Verify that superseded decisions are paired with their replacement and quotes from both meetings."""
    service = BriefingService(ts3012_test_db)
    meetings, _, _, _ = service._get_chronological_meetings("TS3012", "TS3012d")
    changes = service._extract_decision_changes("TS3012", meetings)

    assert len(changes) >= 1
    casing_change = next(c for c in changes if "rubber" in c.updated_decision.lower())
    assert casing_change.previous_meeting_id == "TS3012b"
    assert casing_change.updated_meeting_id == "TS3012c"
    assert len(casing_change.previous_quote.split()) >= 6
    assert len(casing_change.updated_quote.split()) >= 6
    assert casing_change.reason is not None


# -----------------------------------------------------------------------------
# 4. Open Actions and Owner Assignment
# -----------------------------------------------------------------------------
def test_open_actions_and_owner_assignment(ts3012_test_db: Session) -> None:
    """Verify extraction of open actions, explicit owner labels, and unknown owner flags."""
    service = BriefingService(ts3012_test_db)
    meetings, _, _, _ = service._get_chronological_meetings("TS3012", "TS3012d")
    actions = service._extract_open_actions("TS3012", meetings)

    assert len(actions) >= 1
    drawing_action = actions[0]
    assert "drawing" in drawing_action.description.lower()
    assert drawing_action.status == "OPEN"
    assert drawing_action.source_meeting_id == "TS3012c"
    assert len(drawing_action.quote.split()) >= 6
    assert drawing_action.owner_confidence in ["EXPLICIT", "UNKNOWN"]


# -----------------------------------------------------------------------------
# 5. Disagreement Detection and Resolution
# -----------------------------------------------------------------------------
def test_disagreement_detection_and_resolution(ts3012_test_db: Session) -> None:
    """Verify that unresolved disagreements are surfaced with positions and competing speakers."""
    service = BriefingService(ts3012_test_db)
    meetings, _, _, _ = service._get_chronological_meetings("TS3012", "TS3012d")
    disagreements = service._extract_disagreements("TS3012", meetings)

    assert len(disagreements) >= 1
    removable_cover_dispute = disagreements[0]
    assert "removable" in removable_cover_dispute.disputed_issue.lower()
    assert removable_cover_dispute.resolution_status in ["UNRESOLVED", "RESOLVED"]
    assert len(removable_cover_dispute.citations) >= 1


# -----------------------------------------------------------------------------
# 6. Claim-Level Citation Validation
# -----------------------------------------------------------------------------
def test_claim_level_citation_validation(ts3012_test_db: Session) -> None:
    """Verify that all factual citations generated pass the deterministic validator."""
    service = BriefingService(ts3012_test_db)
    res = service.generate_briefing(team_code="TS3012", target_meeting_code="TS3012d")

    assert res.validation_errors == []
    assert res.validation_status == "PASSED"
    assert res.citations_count >= 4

    # Run direct validator check on stored citations
    validator = CitationValidationService(ts3012_test_db)
    for dec in res.structured_payload.get("current_decisions", []):
        cite_dict = {
            "meeting_id": dec["meeting_id"],
            "quote": dec["quote"],
            "speaker_label": dec["speaker_label"],
            "turn_id": dec.get("turn_id"),
        }
        val_res = validator.validate_citation(cite_dict, expected_team="TS3012")
        assert val_res.is_valid is True, f"Failed on decision quote: {dec['quote']}"


# -----------------------------------------------------------------------------
# 7. Missing Meeting Coverage Disclosure
# -----------------------------------------------------------------------------
def test_missing_meeting_coverage_disclosure(db_session: Session) -> None:
    """Verify that gaps in meeting sequences (e.g. missing TS3012b) are disclosed in coverage notices."""
    team = Team(id=uuid.uuid4(), team_code="TS3012")
    m_a = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3012a",
        sequence_letter="a",
        meeting_number=1,
        source_filename="TS3012a.txt",
        source_sha256="sha1",
        raw_text="Meeting A",
    )
    # Note: TS3012b is intentionally NOT added
    m_c = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3012c",
        sequence_letter="c",
        meeting_number=3,
        source_filename="TS3012c.txt",
        source_sha256="sha3",
        raw_text="Meeting C",
    )
    m_d = Meeting(
        id=uuid.uuid4(),
        team_id=team.id,
        meeting_code="TS3012d",
        sequence_letter="d",
        meeting_number=4,
        source_filename="TS3012d.txt",
        source_sha256="sha4",
        raw_text="Meeting D",
    )
    db_session.add_all([team, m_a, m_c, m_d])
    db_session.commit()

    service = BriefingService(db_session)
    res = service.generate_briefing(team_code="TS3012", target_meeting_code="TS3012d")

    assert len(res.structured_payload["missing_coverage"]) >= 1
    assert any("TS3012b" in mc for mc in res.structured_payload["missing_coverage"])
    assert "Data Coverage Notice" in res.content_markdown
    assert "TS3012b" in res.content_markdown


# -----------------------------------------------------------------------------
# 8. Empty or Incomplete Team History
# -----------------------------------------------------------------------------
def test_empty_or_incomplete_team_history(db_session: Session) -> None:
    """Verify graceful handling and empty state disclosure when a team has zero meetings."""
    service = BriefingService(db_session)
    res = service.generate_briefing(team_code="EMPTY_TEAM", target_meeting_code="EMPTY_TEAM_d")

    assert res.team_code == "EMPTY_TEAM"
    assert res.meetings_covered == []
    assert "No historical meeting transcripts were found" in res.content_markdown


# -----------------------------------------------------------------------------
# 9. Briefing Persistence and Versioning
# -----------------------------------------------------------------------------
def test_briefing_persistence_and_versioning(ts3012_test_db: Session) -> None:
    """Verify that briefings are persisted and version increments properly on regeneration."""
    service = BriefingService(ts3012_test_db)

    # Initial generation -> Version 1
    v1 = service.generate_briefing(
        team_code="TS3012", target_meeting_code="TS3012d", regenerate=False
    )
    assert v1.version == 1

    # Calling generate again without regenerate returns cached v1
    v1_cached = service.generate_briefing(
        team_code="TS3012", target_meeting_code="TS3012d", regenerate=False
    )
    assert v1_cached.id == v1.id
    assert v1_cached.version == 1

    # Calling generate with regenerate=True creates Version 2
    v2 = service.generate_briefing(
        team_code="TS3012", target_meeting_code="TS3012d", regenerate=True
    )
    assert v2.id != v1.id
    assert v2.version == 2

    # Query latest returns Version 2
    latest = service.get_latest_briefing("TS3012")
    assert latest is not None
    assert latest.version == 2

    # Query specific briefing by ID
    fetched_v1 = service.get_briefing_by_id(v1.id)
    assert fetched_v1 is not None
    assert fetched_v1.version == 1


# -----------------------------------------------------------------------------
# 10. Briefing API Endpoints
# -----------------------------------------------------------------------------
def test_briefing_api_endpoints(client: TestClient, ts3012_test_db: Session) -> None:
    """Verify all REST API endpoints under /api/v1/briefings/."""
    # 1. Generate endpoint
    gen_payload = {
        "team_code": "TS3012",
        "target_meeting_code": "TS3012d",
        "regenerate": True,
    }
    r_gen = client.post("/api/v1/briefings/generate", json=gen_payload)
    assert r_gen.status_code == 200
    gen_data = r_gen.json()
    assert gen_data["team_code"] == "TS3012"
    assert "content_markdown" in gen_data
    assert gen_data["version"] >= 1
    briefing_id = gen_data["id"]

    # 2. TS3012 convenience endpoint
    r_ts12 = client.get("/api/v1/briefings/ts3012")
    assert r_ts12.status_code == 200
    assert r_ts12.json()["team_code"] == "TS3012"

    # 3. Latest team endpoint
    r_latest = client.get("/api/v1/briefings/TS3012/latest")
    assert r_latest.status_code == 200
    assert r_latest.json()["id"] == gen_data["id"]

    # 4. List versions endpoint
    r_vers = client.get("/api/v1/briefings/TS3012/versions")
    assert r_vers.status_code == 200
    vers_data = r_vers.json()
    assert vers_data["total"] >= 1

    # 5. Get by ID endpoint
    r_id = client.get(f"/api/v1/briefings/{briefing_id}")
    assert r_id.status_code == 200
    assert r_id.json()["id"] == briefing_id

    # 6. Non-existent ID returns 404
    r_404 = client.get(f"/api/v1/briefings/{uuid.uuid4()}")
    assert r_404.status_code == 404


# -----------------------------------------------------------------------------
# 11. Briefing CLI Command
# -----------------------------------------------------------------------------
def test_briefing_cli_command(
    ts3012_test_db: Session,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify that 'catalist brief' executes cleanly and outputs the structured report."""
    import argparse

    from app.cli import handle_brief

    monkeypatch.setattr("app.cli.get_db_session", lambda *args, **kwargs: ts3012_test_db)

    args = argparse.Namespace(
        team="TS3012",
        before="TS3012d",
        regenerate=True,
        format="markdown",
        save=None,
        database_url=None,
    )
    handle_brief(args)
    captured = capsys.readouterr()
    assert "Pre-Meeting Briefing: Team TS3012" in captured.out
    assert "Executive Summary" in captured.out
    assert "Current Decisions" in captured.out
    assert "Open Actions" in captured.out
