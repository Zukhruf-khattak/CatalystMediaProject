import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.schemas.dataset import ParsedMeeting, ParsedSpeaker, ParsedTurn
from app.services.archive_service import compute_sha256, compute_string_sha256

logger = get_logger("app.services.parser")

# Regex for turn start: HH:MM:SS Speaker [A-D]
TURN_HEADER_REGEX = re.compile(r"^(\d{2}:\d{2}:\d{2})\s+(Speaker\s+[A-D])\s*$", re.IGNORECASE)

# Regex for meeting metadata headers
MEETING_CODE_REGEX = re.compile(r"^Meeting:\s*([A-Za-z0-9_-]+)", re.IGNORECASE)
TEAM_CODE_REGEX = re.compile(r"^Team:\s*([A-Za-z0-9_-]+)", re.IGNORECASE)
MEETING_NUM_REGEX = re.compile(r"^Meeting\s*number:\s*(\d+)\s*\(([a-z])\)", re.IGNORECASE)
SPEAKERS_REGEX = re.compile(r"^Speakers:\s*(.+)", re.IGNORECASE)


class TranscriptParseError(AppException):
    """Raised when transcript content is malformed and cannot be parsed."""

    def __init__(self, message: str, details: Optional[Dict[str, str]] = None) -> None:
        super().__init__(message=message, status_code=422, details=details or {})


def parse_timestamp_seconds(time_str: str) -> int:
    """Convert 'HH:MM:SS' string into integer total seconds."""
    parts = time_str.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid timestamp format: '{time_str}', expected 'HH:MM:SS'")
    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def normalize_search_text(text: str) -> str:
    """Normalize transcript text for lexical search indexing without altering raw source."""
    # Collapse multiple whitespace, strip, lowercase
    cleaned = re.sub(r"\s+", " ", text).strip().lower()
    return cleaned


def parse_metadata_header(lines: List[str]) -> Tuple[Dict[str, str], int]:
    """Parse key-value header metadata block.

    Returns:
        Tuple of (metadata dict, index of first line after header).
    """
    metadata: Dict[str, str] = {}
    header_end_idx = 0

    for idx, line in enumerate(lines):
        stripped = line.strip()

        # Stop header parsing if we encounter a turn header
        if TURN_HEADER_REGEX.match(stripped):
            header_end_idx = idx
            break

        m_meeting = MEETING_CODE_REGEX.match(stripped)
        if m_meeting:
            metadata["meeting_code"] = m_meeting.group(1).strip()
            continue

        m_team = TEAM_CODE_REGEX.match(stripped)
        if m_team:
            metadata["team_code"] = m_team.group(1).strip()
            continue

        m_num = MEETING_NUM_REGEX.match(stripped)
        if m_num:
            metadata["meeting_number"] = m_num.group(1).strip()
            metadata["sequence_letter"] = m_num.group(2).strip().lower()
            continue

        m_speakers = SPEAKERS_REGEX.match(stripped)
        if m_speakers:
            metadata["speakers"] = m_speakers.group(1).strip()
            continue

    if header_end_idx == 0:
        # If no turn header found in loop, find the first turn header
        for idx, line in enumerate(lines):
            if TURN_HEADER_REGEX.match(line.strip()):
                header_end_idx = idx
                break

    return metadata, header_end_idx


def parse_speakers_roster(speaker_str: Optional[str]) -> List[ParsedSpeaker]:
    """Parse comma-separated speaker roster from header, e.g. 'Speaker A, Speaker B'."""
    if not speaker_str:
        # Default fallback to 4 AMI speakers
        return [
            ParsedSpeaker(speaker_label=f"Speaker {ch}", speaker_letter=ch)
            for ch in ["A", "B", "C", "D"]
        ]

    speakers: List[ParsedSpeaker] = []
    items = [s.strip() for s in speaker_str.split(",") if s.strip()]
    for item in items:
        # Extract letter from 'Speaker A' or 'A'
        m = re.search(r"Speaker\s+([A-Za-z0-9])", item, re.IGNORECASE)
        letter = m.group(1).upper() if m else item[-1].upper()
        label = f"Speaker {letter}" if not item.lower().startswith("speaker") else item
        speakers.append(ParsedSpeaker(speaker_label=label, speaker_letter=letter))

    return speakers


def parse_turns(lines: List[str], start_idx: int) -> Tuple[List[ParsedTurn], List[str]]:
    """Parse speaker turns starting after header lines.

    Returns:
        Tuple of (list of ParsedTurn objects, list of parser warnings).
    """
    turns: List[ParsedTurn] = []
    warnings: List[str] = []

    current_time_str: Optional[str] = None
    current_time_secs: Optional[int] = None
    current_speaker_label: Optional[str] = None
    current_speaker_letter: Optional[str] = None
    current_utterance_lines: List[str] = []

    last_time_secs = -1

    def flush_turn() -> None:
        nonlocal current_time_str, current_time_secs, current_speaker_label
        nonlocal current_speaker_letter, current_utterance_lines, last_time_secs

        if current_time_str and current_speaker_label:
            # Preserve all internal text and line breaks
            raw_turn_text = "\n".join(current_utterance_lines).strip()
            if not raw_turn_text:
                warnings.append(
                    f"Turn {len(turns)} at {current_time_str} by {current_speaker_label} has empty text; skipped."
                )
            else:
                if current_time_secs is not None and current_time_secs < last_time_secs:
                    warnings.append(
                        f"Non-monotonic timestamp detected at turn {len(turns)}: "
                        f"{current_time_str} ({current_time_secs}s) < previous ({last_time_secs}s)"
                    )
                if current_time_secs is not None:
                    last_time_secs = current_time_secs

                normalized = normalize_search_text(raw_turn_text)
                turn = ParsedTurn(
                    turn_index=len(turns),
                    speaker_label=current_speaker_label,
                    speaker_letter=current_speaker_letter or current_speaker_label[-1].upper(),
                    start_time_str=current_time_str,
                    start_time_seconds=current_time_secs or 0,
                    raw_text=raw_turn_text,
                    normalized_text=normalized,
                )
                turns.append(turn)

        current_utterance_lines = []

    for idx in range(start_idx, len(lines)):
        line = lines[idx]
        stripped = line.strip()

        m_turn = TURN_HEADER_REGEX.match(stripped)
        if m_turn:
            flush_turn()
            current_time_str = m_turn.group(1)
            try:
                current_time_secs = parse_timestamp_seconds(current_time_str)
            except ValueError as e:
                warnings.append(f"Line {idx + 1}: {e}")
                current_time_secs = 0

            label_raw = m_turn.group(2)
            # Normalize casing to 'Speaker X'
            letter = label_raw.split()[-1].upper()
            current_speaker_label = f"Speaker {letter}"
            current_speaker_letter = letter
        else:
            if current_time_str is not None:
                current_utterance_lines.append(line)

    # Flush final turn
    flush_turn()

    # Calculate end times based on next turn's start time
    for i in range(len(turns) - 1):
        # We can construct updated turn with end_time_seconds
        next_start = turns[i + 1].start_time_seconds
        turns[i] = turns[i].model_copy(update={"end_time_seconds": next_start})

    return turns, warnings


def parse_transcript(
    content: str, filename: str, file_sha256: Optional[str] = None
) -> ParsedMeeting:
    """Parse complete transcript content into typed ParsedMeeting model."""
    if not content or not content.strip():
        raise TranscriptParseError(
            f"Transcript file '{filename}' is empty",
            details={"filename": filename},
        )

    lines = content.splitlines()
    metadata, header_end_idx = parse_metadata_header(lines)

    meeting_code = metadata.get("meeting_code")
    # If meeting_code missing in header, infer from filename (e.g. ES2002a.txt -> ES2002a)
    if not meeting_code:
        base_name = Path(filename).stem
        if re.match(r"^[A-Za-z0-9_-]+$", base_name):
            meeting_code = base_name
        else:
            raise TranscriptParseError(
                f"Missing required 'Meeting:' header and cannot derive code from filename: {filename}",
                details={"filename": filename},
            )

    team_code = metadata.get("team_code")
    # If team_code missing in header, derive from meeting code by stripping last char if it's letter
    if not team_code:
        if len(meeting_code) > 1 and meeting_code[-1].isalpha():
            team_code = meeting_code[:-1]
        else:
            team_code = meeting_code

    meeting_num = int(metadata["meeting_number"]) if "meeting_number" in metadata else None
    seq_letter = metadata.get("sequence_letter")
    if not seq_letter and len(meeting_code) > 1 and meeting_code[-1].isalpha():
        seq_letter = meeting_code[-1].lower()

    speakers = parse_speakers_roster(metadata.get("speakers"))

    turns, warnings = parse_turns(lines, header_end_idx)

    if not turns:
        raise TranscriptParseError(
            f"No valid speaker turns found in transcript: {filename}",
            details={"filename": filename},
        )

    # Calculate aggregate stats
    total_words = sum(len(t.raw_text.split()) for t in turns)
    last_turn_seconds = float(turns[-1].start_time_seconds) if turns else 0.0
    sha256_hash = file_sha256 or compute_string_sha256(content)

    return ParsedMeeting(
        meeting_code=meeting_code,
        team_code=team_code,
        meeting_number=meeting_num,
        sequence_letter=seq_letter,
        speakers=speakers,
        turns=turns,
        source_filename=Path(filename).name,
        source_sha256=sha256_hash,
        word_count=total_words,
        total_turns=len(turns),
        raw_text=content,
        duration_seconds=last_turn_seconds,
        parser_warnings=warnings,
    )


def parse_transcript_file(file_path: Path) -> ParsedMeeting:
    """Read and parse transcript from a file path."""
    if not file_path.exists():
        raise TranscriptParseError(
            f"File does not exist: {file_path}",
            details={"path": str(file_path)},
        )

    sha256_hash = compute_sha256(file_path)
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    return parse_transcript(content=content, filename=file_path.name, file_sha256=sha256_hash)
