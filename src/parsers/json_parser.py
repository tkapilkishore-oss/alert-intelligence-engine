"""JSON Alert Parser module for Alert Intelligence Engine."""

import json
from typing import Any, Dict, List, Optional

from src.logger import get_logger
from src.parsers.base_parser import BaseParser
from src.schema import ParsedAlert

logger = get_logger(__name__)


class JsonParser(BaseParser):
    """Parser for JSON format disaster alerts."""

    FIELD_ALIASES: Dict[str, List[str]] = {
        "raw_hazard": ["hazard", "event", "warningType"],
        "raw_severity": ["severity", "level", "severity_text"],
        "raw_urgency": ["urgency"],
        "raw_certainty": ["certainty"],
        "raw_location": ["location", "area", "district"],
        "raw_start_time": ["valid_from", "onset", "startTime"],
        "raw_end_time": ["valid_to", "endTime", "expires"],
        "raw_action": ["recommended_action", "advice", "instruction"],
    }

    def parse(self, raw_data: Any) -> List[ParsedAlert]:
        """Parse raw JSON data into a list of ParsedAlert intermediate objects.

        Args:
            raw_data: Raw input data (List[dict], dict, or JSON string).

        Returns:
            List[ParsedAlert]: List of extracted unnormalized ParsedAlert records.
        """
        records = self._normalize_input(raw_data)
        parsed_alerts: List[ParsedAlert] = []

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                logger.warning(f"Skipping record at index {index}: Expected dict, got {type(record).__name__}")
                continue

            try:
                alert = self._parse_record(record)
                parsed_alerts.append(alert)
            except Exception as e:
                logger.warning(f"Failed to parse record at index {index}: {e}")

        return parsed_alerts

    def _normalize_input(self, raw_data: Any) -> List[Any]:
        """Normalize raw input into a list of records."""
        if isinstance(raw_data, str):
            try:
                parsed = json.loads(raw_data)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    return [parsed]
                else:
                    logger.warning(f"JSON string parsed to non-collection type: {type(parsed).__name__}")
                    return []
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON string input: {e}")
                return []
        elif isinstance(raw_data, list):
            return raw_data
        elif isinstance(raw_data, dict):
            return [raw_data]
        else:
            logger.warning(f"Unsupported input type for JsonParser: {type(raw_data).__name__}")
            return []

    def _parse_record(self, record: Dict[str, Any]) -> ParsedAlert:
        """Extract raw fields from a single record dict into a ParsedAlert."""
        extracted_fields: Dict[str, Optional[str]] = {}

        for target_field, aliases in self.FIELD_ALIASES.items():
            value = None
            for alias in aliases:
                if alias in record and record[alias] is not None:
                    value = str(record[alias])
                    break
            extracted_fields[target_field] = value

        source = str(record.get("source", "JSON Feed"))

        return ParsedAlert(
            raw_hazard=extracted_fields["raw_hazard"],
            raw_severity=extracted_fields["raw_severity"],
            raw_urgency=extracted_fields["raw_urgency"],
            raw_certainty=extracted_fields["raw_certainty"],
            raw_location=extracted_fields["raw_location"],
            raw_start_time=extracted_fields["raw_start_time"],
            raw_end_time=extracted_fields["raw_end_time"],
            raw_action=extracted_fields["raw_action"],
            source=source,
            source_format="json",
            raw_payload=record,
        )
