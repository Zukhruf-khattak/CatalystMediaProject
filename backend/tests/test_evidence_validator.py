from app.models.dataset import Speaker, TranscriptTurn
from app.services.evidence_validator import EvidenceValidator, normalize_for_quote_match


def test_normalize_for_quote_match():
    text = "  So   we are   deciding \n on titanium  casing.\t"
    norm = normalize_for_quote_match(text)
    assert norm == "so we are deciding on titanium casing."


def test_validate_quote_in_text_success():
    validator = EvidenceValidator(min_quote_words=6)
    source = "I think we should definitely go with the titanium case for our remote."
    quote = "we should definitely go with the titanium case"

    is_valid, error = validator.validate_quote_in_text(quote, source)
    assert is_valid is True
    assert error is None


def test_validate_quote_too_short():
    validator = EvidenceValidator(min_quote_words=6)
    source = "I think we should definitely go with the titanium case."
    quote = "with the titanium case"  # 4 words

    is_valid, error = validator.validate_quote_in_text(quote, source)
    assert is_valid is False
    assert "minimum required is 6" in error


def test_validate_quote_modified_or_fabricated():
    validator = EvidenceValidator(min_quote_words=6)
    source = "I think we should definitely go with the titanium case."
    quote = "I think we should definitely choose the titanium case"  # "choose" instead of "go with"

    is_valid, error = validator.validate_quote_in_text(quote, source)
    assert is_valid is False
    assert "not found verbatim" in error


def test_validate_memory_evidence_with_speaker_match():
    validator = EvidenceValidator(min_quote_words=6)
    speaker = Speaker(speaker_label="Speaker B", speaker_letter="B")
    turn = TranscriptTurn(
        turn_index=5,
        start_time_str="00:01:20",
        start_time_seconds=80,
        raw_text="Let us make sure the battery is rechargeable and kinetic.",
        normalized_text="let us make sure the battery is rechargeable and kinetic",
        speaker=speaker,
    )

    is_valid, error = validator.validate_memory_evidence(
        quote="make sure the battery is rechargeable and kinetic",
        speaker_label="Speaker B",
        turn=turn,
    )
    assert is_valid is True
    assert error is None


def test_validate_memory_evidence_speaker_mismatch():
    validator = EvidenceValidator(min_quote_words=6)
    speaker = Speaker(speaker_label="Speaker B", speaker_letter="B")
    turn = TranscriptTurn(
        turn_index=5,
        start_time_str="00:01:20",
        start_time_seconds=80,
        raw_text="Let us make sure the battery is rechargeable and kinetic.",
        normalized_text="let us make sure the battery is rechargeable and kinetic",
        speaker=speaker,
    )

    is_valid, error = validator.validate_memory_evidence(
        quote="make sure the battery is rechargeable and kinetic",
        speaker_label="Speaker C",  # Mismatch
        turn=turn,
    )
    assert is_valid is False
    assert "does not match turn speaker" in error


def test_validate_action_owner_present_in_turn():
    validator = EvidenceValidator(min_quote_words=6)
    turn = TranscriptTurn(
        turn_index=10,
        start_time_str="00:03:00",
        start_time_seconds=180,
        raw_text="David will investigate the rubber casing options by next meeting.",
        normalized_text="david will investigate the rubber casing options by next meeting",
    )

    is_valid, error = validator.validate_memory_evidence(
        quote="David will investigate the rubber casing options by next meeting",
        speaker_label="Speaker A",
        turn=turn,
        owner="David",
    )
    assert is_valid is True


def test_validate_action_owner_not_present_in_turn():
    validator = EvidenceValidator(min_quote_words=6)
    turn = TranscriptTurn(
        turn_index=10,
        start_time_str="00:03:00",
        start_time_seconds=180,
        raw_text="Someone needs to check the battery specifications before Thursday.",
        normalized_text="someone needs to check the battery specifications before thursday",
    )

    is_valid, error = validator.validate_memory_evidence(
        quote="Someone needs to check the battery specifications before Thursday",
        speaker_label="Speaker A",
        turn=turn,
        owner="Alice",  # Alice is not mentioned anywhere in turn text
    )
    assert is_valid is False
    assert "not mentioned in the supporting transcript turn" in error
