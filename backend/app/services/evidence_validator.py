import re
from typing import Optional, Tuple

from app.core.logging import get_logger
from app.models.dataset import TranscriptTurn

logger = get_logger("app.services.evidence_validator")


def normalize_for_quote_match(text: str) -> str:
    """Normalize whitespace and casing for exact quotation substring comparison.

    Collapses consecutive whitespace, tabs, and newlines to a single space, strips edges,
    and converts to lowercase. Punctuation within speech is retained.
    """
    if not text:
        return ""
    # Replace newlines, tabs, and multiple spaces with a single space
    cleaned = re.sub(r"\s+", " ", text).strip().lower()
    return cleaned


class EvidenceValidator:
    """Deterministic validator enforcing that extracted memories strictly cite verbatim transcript turns."""

    def __init__(self, min_quote_words: int = 6) -> None:
        self.min_quote_words = min_quote_words

    def validate_quote_in_text(self, quote: str, source_text: str) -> Tuple[bool, Optional[str]]:
        """Verify that quote appears verbatim as an exact substring within source_text."""
        if not quote or not quote.strip():
            return False, "Quotation cannot be empty."

        words = quote.strip().split()
        if len(words) < self.min_quote_words:
            return (
                False,
                f"Quotation has only {len(words)} words; minimum required is {self.min_quote_words}.",
            )

        norm_quote = normalize_for_quote_match(quote)
        norm_source = normalize_for_quote_match(source_text)

        if norm_quote not in norm_source:
            return (
                False,
                "Quotation was not found verbatim in the referenced transcript turn (modified or fabricated).",
            )

        return True, None

    def validate_memory_evidence(
        self,
        quote: str,
        speaker_label: str,
        turn: TranscriptTurn,
        owner: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Validate candidate memory against the actual database TranscriptTurn record."""
        # 1. Validate quote exists in turn text
        valid_quote, reason = self.validate_quote_in_text(quote, turn.raw_text)
        if not valid_quote:
            return False, reason

        # 2. Validate speaker label consistency
        norm_expected_speaker = turn.speaker.speaker_label.strip().lower() if turn.speaker else None
        norm_given_speaker = speaker_label.strip().lower()

        if norm_expected_speaker and norm_given_speaker != norm_expected_speaker:
            # Also allow matching just the letter, e.g. "Speaker B" vs "B"
            expected_letter = norm_expected_speaker.split()[-1]
            given_letter = norm_given_speaker.split()[-1]
            if expected_letter != given_letter:
                return (
                    False,
                    f"Speaker '{speaker_label}' does not match turn speaker '{turn.speaker.speaker_label}'.",
                )

        # 3. Action ownership validation: do not infer owner without textual evidence
        if owner and owner.strip():
            norm_owner = owner.strip().lower()
            norm_turn = turn.raw_text.lower()
            # The owner name, role, or speaker letter must appear in the turn text
            owner_tokens = norm_owner.split()
            if not any(token in norm_turn for token in owner_tokens):
                return (
                    False,
                    f"Action owner '{owner}' is not mentioned in the supporting transcript turn.",
                )

        return True, None


_validator_instance: Optional[EvidenceValidator] = None


def get_evidence_validator() -> EvidenceValidator:
    """Return singleton EvidenceValidator."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = EvidenceValidator(min_quote_words=6)
    return _validator_instance
