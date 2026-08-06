"""Natural Language Entry Layer processor for Alert Intelligence Engine."""

from typing import Optional

from src.gemini_extractor import GeminiExtractor
from src.logger import get_logger
from src.schema import ParsedAlert

logger = get_logger(__name__)


class NaturalLanguageProcessor:
    """Processor converting free-form user natural language into structured ParsedAlert representation."""

    def __init__(self, gemini_extractor: Optional[GeminiExtractor] = None) -> None:
        """Initialize NaturalLanguageProcessor with optional GeminiExtractor.

        Args:
            gemini_extractor: Optional GeminiExtractor instance override.
        """
        self._gemini_extractor = gemini_extractor or GeminiExtractor()

    def process(self, text: str) -> ParsedAlert:
        """Convert free-form natural language text into a ParsedAlert for pipeline processing.

        Args:
            text: Free-form user disaster alert text.

        Returns:
            ParsedAlert: Intermediate alert representation enriched by Gemini extraction.
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

        parsed = ParsedAlert(
            source="Natural Language Entry Layer",
            source_format="plaintext",
            raw_payload={"original_text": cleaned_text if isinstance(text, str) else str(text)},
            parse_warnings=warnings,
        )

        if cleaned_text:
            parsed = self._gemini_extractor.enrich(parsed)

        parsed.raw_payload["_nlp_processed"] = True
        return parsed

