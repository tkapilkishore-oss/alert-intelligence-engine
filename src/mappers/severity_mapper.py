"""Severity Mapper module for Stage 7 Normalization Engine."""

import csv
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from src.constants import SEVERITY_REFERENCE_FILE
from src.logger import get_logger
from src.schema import SeverityType

logger = get_logger(__name__)


class SeverityMapper:
    """Mapper responsible for mapping raw severity strings to canonical SeverityType using reference CSV data."""

    def __init__(self, csv_path: Optional[Union[str, Path]] = None) -> None:
        """Initialize SeverityMapper by loading reference CSV into memory once.

        Args:
            csv_path: Path to severity reference CSV file. Defaults to SEVERITY_REFERENCE_FILE constant.
        """
        self._csv_path = Path(csv_path) if csv_path else SEVERITY_REFERENCE_FILE
        self._mapping_cache: Dict[str, SeverityType] = {}
        self._load_reference_data()

    def _load_reference_data(self) -> None:
        """Load severity mappings from CSV into internal memory cache."""
        if not self._csv_path.exists():
            logger.error(f"Severity mapping CSV file not found: {self._csv_path}")
            return

        try:
            with open(self._csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    term = row.get("raw_severity_term", "").strip()
                    canonical = row.get("canonical_severity", "").strip()
                    if term and canonical:
                        self._mapping_cache[term.lower()] = canonical  # type: ignore[assignment]
        except Exception as e:
            logger.error(f"Failed to load severity mapping CSV {self._csv_path}: {e}")

    def map_severity(self, raw_severity: Optional[str]) -> Tuple[SeverityType, Optional[str]]:
        """Map raw severity string to canonical SeverityType.

        Args:
            raw_severity: Raw severity string from ParsedAlert.

        Returns:
            Tuple[SeverityType, Optional[str]]: Canonical severity enum and an optional parse warning if unknown.
        """
        if not raw_severity or not raw_severity.strip():
            return "Unknown", "Missing raw severity; mapped to 'Unknown'"

        cleaned = raw_severity.strip().lower()

        if cleaned in self._mapping_cache:
            return self._mapping_cache[cleaned], None

        warning = f"Unknown severity term '{raw_severity}'; mapped to 'Unknown'"
        logger.info(warning)
        return "Unknown", warning
