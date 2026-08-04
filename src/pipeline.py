"""Pipeline Orchestration Engine for Alert Intelligence Engine."""

from typing import Any, Dict, List, Optional

from src.deduplicator import DeduplicationEngine
from src.gemini_extractor import GeminiExtractor
from src.logger import get_logger
from src.nlp_processor import NaturalLanguageProcessor
from src.normalization import NormalizationEngine
from src.parsers.base_parser import BaseParser
from src.parsers.cap_parser import CapParser
from src.parsers.json_parser import JsonParser
from src.parsers.plaintext_parser import PlaintextParser
from src.parsers.rss_parser import RssParser
from src.schema import NormalizedAlert, ParsedAlert
from src.validator import ValidationEngine

logger = get_logger(__name__)


class AlertPipeline:
    """Pipeline Orchestration Engine connecting parsing, validation, normalization, and deduplication."""

    def __init__(
        self,
        validator: Optional[ValidationEngine] = None,
        gemini_extractor: Optional[GeminiExtractor] = None,
        normalization_engine: Optional[NormalizationEngine] = None,
        deduplication_engine: Optional[DeduplicationEngine] = None,
        nlp_processor: Optional[NaturalLanguageProcessor] = None,
    ) -> None:
        """Initialize AlertPipeline with processing engines.

        Args:
            validator: Optional ValidationEngine instance.
            gemini_extractor: Optional GeminiExtractor instance.
            normalization_engine: Optional NormalizationEngine instance.
            deduplication_engine: Optional DeduplicationEngine instance.
            nlp_processor: Optional NaturalLanguageProcessor instance.
        """
        self._validator = validator or ValidationEngine()
        self._gemini_extractor = gemini_extractor or GeminiExtractor()
        self._normalization_engine = normalization_engine or NormalizationEngine()
        self._deduplication_engine = deduplication_engine or DeduplicationEngine()
        self._nlp_processor = nlp_processor or NaturalLanguageProcessor()
        self._parsers: Dict[str, BaseParser] = {
            "json": JsonParser(),
            "cap_xml": CapParser(),
            "rss": RssParser(),
            "plaintext": PlaintextParser(),
        }

    def process(self, raw_data: Any, source_format: str) -> List[NormalizedAlert]:
        """Execute processing pipeline on raw inputs.

        Pipeline Execution Order:
            1. Select parser based on source_format (_get_parser)
            2. Parse raw input (_parse)
            3. Structural Validation (_validate_parsed)
            4. Gemini Fallback (_gemini_enrich)
            5. Normalization (_normalize)
            6. Schema Validation (_validate_normalized)
            7. Deduplication (_deduplicate)
            8. Return List[NormalizedAlert]

        Args:
            raw_data: Raw input data (dict, list, str, bytes, XML element, etc.).
            source_format: Identifier string ("json", "cap_xml", "rss", "plaintext").

        Returns:
            List[NormalizedAlert]: List of deduplicated, schema-validated normalized alerts.

        Raises:
            ValueError: If source_format is not supported.
        """
        parser = self._get_parser(source_format)
        parsed_alerts = self._parse(parser, raw_data)
        structurally_valid = self._validate_parsed(parsed_alerts)
        enriched_alerts = self._gemini_enrich(structurally_valid)
        normalized_alerts = self._normalize(enriched_alerts)
        schema_valid_alerts = self._validate_normalized(normalized_alerts)
        return self._deduplicate(schema_valid_alerts)

    def process_natural_language(self, text: str) -> List[NormalizedAlert]:
        """Process free-form user natural language input through NaturalLanguageProcessor and pipeline.

        Pipeline Execution Order:
            1. NaturalLanguageProcessor converts text to ParsedAlert
            2. Structural Validation (_validate_parsed)
            3. Gemini Fallback Enrichment (_gemini_enrich)
            4. Field Normalization (_normalize)
            5. Final Schema Validation (_validate_normalized)
            6. Batch Deduplication (_deduplicate)
            7. Return List[NormalizedAlert]

        Args:
            text: Free-form user disaster alert text string.

        Returns:
            List[NormalizedAlert]: List of deduplicated, schema-validated normalized alerts.
        """
        parsed_alert = self._nlp_processor.process(text)
        structurally_valid = self._validate_parsed([parsed_alert])
        enriched_alerts = self._gemini_enrich(structurally_valid)
        normalized_alerts = self._normalize(enriched_alerts)
        schema_valid_alerts = self._validate_normalized(normalized_alerts)
        return self._deduplicate(schema_valid_alerts)

    def _get_parser(self, source_format: str) -> BaseParser:
        """Select format parser based on source_format string.

        Args:
            source_format: Format name ("json", "cap_xml", "rss", "plaintext").

        Returns:
            BaseParser: Format-specific parser instance.

        Raises:
            ValueError: If source_format is unsupported or empty.
        """
        if not isinstance(source_format, str) or not source_format.strip():
            raise ValueError(f"Invalid source format: '{source_format}'. Expected string.")

        fmt_key = source_format.strip().lower()
        if fmt_key not in self._parsers:
            valid_formats = ", ".join(sorted(self._parsers.keys()))
            raise ValueError(
                f"Unsupported source format: '{source_format}'. Supported formats: {valid_formats}"
            )

        return self._parsers[fmt_key]

    def _parse(self, parser: BaseParser, raw_data: Any) -> List[ParsedAlert]:
        """Parse raw input using selected parser.

        Args:
            parser: BaseParser instance.
            raw_data: Raw input payload.

        Returns:
            List[ParsedAlert]: Intermediate ParsedAlert records.
        """
        if raw_data is None:
            return []
        return parser.parse(raw_data)

    def _validate_parsed(self, alerts: List[ParsedAlert]) -> List[ParsedAlert]:
        """Perform structural validation on ParsedAlert objects.

        Args:
            alerts: List of raw ParsedAlert records.

        Returns:
            List[ParsedAlert]: Structurally valid ParsedAlert records with warnings updated.
        """
        valid_alerts: List[ParsedAlert] = []
        for alert in alerts:
            res = self._validator.validate_structure(alert)
            if res.is_valid:
                valid_alert = alert.model_copy(update={"parse_warnings": res.warnings})
                valid_alerts.append(valid_alert)
            else:
                logger.warning(
                    f"Skipping record failed structural validation (source='{alert.source}'): {res.errors}"
                )
        return valid_alerts

    def _gemini_enrich(self, alerts: List[ParsedAlert]) -> List[ParsedAlert]:
        """Enrich incomplete alerts using Gemini fallback extractor.

        Args:
            alerts: Structurally valid ParsedAlert records.

        Returns:
            List[ParsedAlert]: Enriched ParsedAlert records.
        """
        return [self._gemini_extractor.enrich(alert) for alert in alerts]

    def _normalize(self, alerts: List[ParsedAlert]) -> List[NormalizedAlert]:
        """Convert ParsedAlert records into NormalizedAlert objects.

        Args:
            alerts: Enriched ParsedAlert records.

        Returns:
            List[NormalizedAlert]: Unvalidated NormalizedAlert records.
        """
        return [self._normalization_engine.normalize(alert) for alert in alerts]

    def _validate_normalized(self, alerts: List[NormalizedAlert]) -> List[NormalizedAlert]:
        """Perform schema validation on NormalizedAlert objects.

        Args:
            alerts: Unvalidated NormalizedAlert records.

        Returns:
            List[NormalizedAlert]: Schema-compliant NormalizedAlert records with warnings updated.
        """
        valid_alerts: List[NormalizedAlert] = []
        for alert in alerts:
            res = self._validator.validate_schema(alert)
            if res.is_valid:
                valid_alert = alert.model_copy(update={"parse_warnings": res.warnings})
                valid_alerts.append(valid_alert)
            else:
                logger.warning(
                    f"Skipping normalized alert failed schema validation (id='{alert.alert_id}'): {res.errors}"
                )
        return valid_alerts

    def _deduplicate(self, alerts: List[NormalizedAlert]) -> List[NormalizedAlert]:
        """Identify duplicates across batch using DeduplicationEngine.

        Args:
            alerts: Schema-validated NormalizedAlert records.

        Returns:
            List[NormalizedAlert]: Batch with duplicate flags set appropriately.
        """
        return self._deduplication_engine.deduplicate(alerts)


# Backward compatibility alias for Stage 1 foundation tests
Pipeline = AlertPipeline
