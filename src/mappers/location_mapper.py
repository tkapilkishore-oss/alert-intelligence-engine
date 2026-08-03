"""Location Mapper module for Stage 7 Normalization Engine."""

import csv
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from src.constants import LOCATION_REFERENCE_FILE
from src.logger import get_logger

logger = get_logger(__name__)


class LocationMapper:
    """Mapper responsible for resolving raw location strings to location_id and location_name using reference CSV data."""

    def __init__(self, csv_path: Optional[Union[str, Path]] = None) -> None:
        """Initialize LocationMapper by loading reference CSV into memory once.

        Args:
            csv_path: Path to location reference CSV file. Defaults to LOCATION_REFERENCE_FILE constant.
        """
        self._csv_path = Path(csv_path) if csv_path else LOCATION_REFERENCE_FILE
        # Cache mapping: lowercase location_name -> (canonical_location_name, location_id)
        self._location_cache: Dict[str, Tuple[str, str]] = {}
        self._load_reference_data()

    def _load_reference_data(self) -> None:
        """Load location mappings from CSV into internal memory cache."""
        if not self._csv_path.exists():
            logger.error(f"Location reference CSV file not found: {self._csv_path}")
            return

        try:
            with open(self._csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    loc_id = row.get("location_id", "").strip()
                    loc_name = row.get("location_name", "").strip()
                    if loc_id and loc_name:
                        self._location_cache[loc_name.lower()] = (loc_name, loc_id)
        except Exception as e:
            logger.error(f"Failed to load location reference CSV {self._csv_path}: {e}")

    def map_location(self, raw_location: Optional[str]) -> Tuple[str, Optional[str], Optional[str]]:
        """Resolve raw location string into canonical location_name, location_id, and optional parse_warning.

        Args:
            raw_location: Raw location string from ParsedAlert.

        Returns:
            Tuple[str, Optional[str], Optional[str]]:
                - location_name (str)
                - location_id (Optional[str], None if no match)
                - parse_warning (Optional[str], present if unmapped/missing)
        """
        if not raw_location or not raw_location.strip():
            warning = "Missing raw location"
            logger.info(warning)
            return "Unknown Location", None, warning

        cleaned = raw_location.strip()
        cleaned_lower = cleaned.lower()

        if cleaned_lower in self._location_cache:
            canonical_name, location_id = self._location_cache[cleaned_lower]
            return canonical_name, location_id, None

        warning = f"Unknown location: '{raw_location}'"
        logger.info(warning)
        return cleaned, None, warning
