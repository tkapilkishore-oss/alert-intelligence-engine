"""Natural Language Entry Layer processor for Alert Intelligence Engine."""

from typing import Optional

from src.logger import get_logger
from src.schema import ParsedAlert

logger = get_logger(__name__)


class NaturalLanguageProcessor:
    """Processor converting free-form user natural language into structured ParsedAlert representation."""

    def process(self, text: str) -> ParsedAlert:
        """Convert free-form natural language text into a ParsedAlert for pipeline processing.

        Args:
            text: Free-form user disaster alert text.

        Returns:
            ParsedAlert: Unnormalized intermediate alert representation with original text packaged in raw_payload.
        """
        warnings = []
        cleaned_text = ""

        if not isinstance(text, str):
            warnings.append(f"Invalid input type: expected str, got {type(text).__name__}")
            logger.warning(f"NaturalLanguageProcessor received non-string input: {type(text).__name__}")
        else:
            cleaned_text = text.strip()
            if not cleaned_text:
                warnings.append("Empty or whitespace natural language input text")
                logger.warning("NaturalLanguageProcessor received empty/whitespace input.")

        return ParsedAlert(
            source="Natural Language Entry Layer",
            source_format="plaintext",
            raw_payload={"original_text": cleaned_text if isinstance(text, str) else str(text)},
            parse_warnings=warnings,
        )
