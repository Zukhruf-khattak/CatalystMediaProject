import pytest

from app.services.parser_service import (
    normalize_search_text,
    parse_metadata_header,
    parse_speakers_roster,
    parse_timestamp_seconds,
    parse_transcript,
    parse_turns,
)

SAMPLE_VALID_TRANSCRIPT = """Meeting: ES2002a
Team: ES2002
Meeting number: 1 (a) of the team's four meetings
Speakers: Speaker A, Speaker B, Speaker C, Speaker D
Times: turn start time from the start of the recording (HH:MM:SS)
Source: AMI Meeting Corpus, CC BY 4.0

00:00:50 Speaker B
Okay. Right. Um well this is the kick-off meeting for our our project.
Um and um this is just what we're gonna be doing over the next twenty five minutes.

00:01:06 Speaker D
Mm-hmm. Great.

00:01:17 Speaker A
Hi, I'm David and I'm supposed to be an industrial designer.
"""


def test_parse_timestamp_seconds() -> None:
    assert parse_timestamp_seconds("00:00:00") == 0
    assert parse_timestamp_seconds("00:00:50") == 50
    assert parse_timestamp_seconds("01:05:23") == 3600 + 5 * 60 + 23
    with pytest.raises(ValueError):
        parse_timestamp_seconds("invalid")


def test_normalize_search_text() -> None:
    raw = "  Okay.   Right.\nUm  well this is   great!  "
    normalized = normalize_search_text(raw)
    assert normalized == "okay. right. um well this is great!"


def test_parse_valid_meeting_header() -> None:
    lines = SAMPLE_VALID_TRANSCRIPT.splitlines()
    metadata, header_end = parse_metadata_header(lines)
    assert metadata["meeting_code"] == "ES2002a"
    assert metadata["team_code"] == "ES2002"
    assert metadata["meeting_number"] == "1"
    assert metadata["sequence_letter"] == "a"
    assert "Speaker A" in metadata["speakers"]
    assert header_end > 0


def test_parse_valid_speaker_roster() -> None:
    roster_str = "Speaker A, Speaker B, Speaker C, Speaker D"
    speakers = parse_speakers_roster(roster_str)
    assert len(speakers) == 4
    assert [s.speaker_label for s in speakers] == [
        "Speaker A",
        "Speaker B",
        "Speaker C",
        "Speaker D",
    ]
    assert [s.speaker_letter for s in speakers] == ["A", "B", "C", "D"]


def test_parse_timestamped_turns() -> None:
    lines = SAMPLE_VALID_TRANSCRIPT.splitlines()
    _, header_end = parse_metadata_header(lines)
    turns, warnings = parse_turns(lines, header_end)

    assert len(turns) == 3
    assert len(warnings) == 0

    # Verify first turn
    assert turns[0].turn_index == 0
    assert turns[0].speaker_label == "Speaker B"
    assert turns[0].speaker_letter == "B"
    assert turns[0].start_time_str == "00:00:50"
    assert turns[0].start_time_seconds == 50
    assert turns[0].end_time_seconds == 66  # 00:01:06 is 66 seconds


def test_preserve_multiline_turn_text_exactly() -> None:
    lines = SAMPLE_VALID_TRANSCRIPT.splitlines()
    _, header_end = parse_metadata_header(lines)
    turns, _ = parse_turns(lines, header_end)

    expected_text = (
        "Okay. Right. Um well this is the kick-off meeting for our our project.\n"
        "Um and um this is just what we're gonna be doing over the next twenty five minutes."
    )
    assert turns[0].raw_text == expected_text
    assert "Um well this is the kick-off meeting" in turns[0].raw_text


def test_preserve_speaker_labels() -> None:
    lines = SAMPLE_VALID_TRANSCRIPT.splitlines()
    _, header_end = parse_metadata_header(lines)
    turns, _ = parse_turns(lines, header_end)

    labels = [t.speaker_label for t in turns]
    assert labels == ["Speaker B", "Speaker D", "Speaker A"]


def test_handle_blank_lines() -> None:
    transcript = """Meeting: TS3001a
Team: TS3001

00:00:10 Speaker A


Hello everyone.


00:00:20 Speaker B

Hi.
"""
    parsed = parse_transcript(transcript, "TS3001a.txt")
    assert parsed.total_turns == 2
    assert parsed.turns[0].raw_text == "Hello everyone."
    assert parsed.turns[1].raw_text == "Hi."


def test_handle_missing_team_metadata() -> None:
    # Team header missing; should derive from meeting code ES2003b -> ES2003
    transcript = """Meeting: ES2003b

00:00:10 Speaker A
Testing turn text.
"""
    parsed = parse_transcript(transcript, "ES2003b.txt")
    assert parsed.meeting_code == "ES2003b"
    assert parsed.team_code == "ES2003"
    assert parsed.sequence_letter == "b"


def test_handle_malformed_timestamp_warning() -> None:
    transcript = """Meeting: TS3002a
Team: TS3002

99:99 Speaker A
Some turn text.

00:01:00 Speaker B
Second turn text.
"""
    # 99:99 does not match HH:MM:SS regex, so it won't be parsed as a turn header
    parsed = parse_transcript(transcript, "TS3002a.txt")
    assert parsed.total_turns == 1
    assert parsed.turns[0].speaker_label == "Speaker B"


def test_handle_empty_turn_text_skipped_with_warning() -> None:
    transcript = """Meeting: TS3003a
Team: TS3003

00:00:10 Speaker A

00:00:20 Speaker B
Real turn text here.
"""
    parsed = parse_transcript(transcript, "TS3003a.txt")
    assert parsed.total_turns == 1
    assert parsed.turns[0].speaker_label == "Speaker B"
    assert any("empty text" in w for w in parsed.parser_warnings)


def test_detect_out_of_order_timestamps() -> None:
    transcript = """Meeting: TS3004a
Team: TS3004

00:02:00 Speaker A
First utterance.

00:01:00 Speaker B
Utterance with earlier timestamp.
"""
    parsed = parse_transcript(transcript, "TS3004a.txt")
    assert parsed.total_turns == 2
    assert any("Non-monotonic timestamp detected" in w for w in parsed.parser_warnings)


def test_transcript_text_resembling_header_not_split() -> None:
    transcript = """Meeting: TS3005a
Team: TS3005

00:00:10 Speaker A
We talked about Meeting: TS3005b and Speaker B yesterday at 12:00:00.
And we also looked at 00:00:50 Speaker C as an example text in our slides.

00:01:00 Speaker B
Yes, exactly.
"""
    parsed = parse_transcript(transcript, "TS3005a.txt")
    # Should only split on genuine turn header lines
    # Notice: 00:00:50 Speaker C appears on its own line in the utterance or mid-sentence
    # If mid-sentence, it shouldn't split
    assert parsed.total_turns == 2
    assert "We talked about Meeting: TS3005b" in parsed.turns[0].raw_text
