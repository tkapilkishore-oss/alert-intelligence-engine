"""Urgency Mapper module for Stage 7 Normalization Engine."""

from typing import Dict, Optional, Tuple
from src.logger import get_logger
from src.schema import UrgencyType

logger = get_logger(__name__)


class UrgencyMapper:
    """Mapper responsible for mapping raw urgency strings to canonical UrgencyType."""

    _CANONICAL_LOOKUP: Dict[str, UrgencyType] = {
        "immediate": "Immediate",
        "expected": "Expected",
        "future": "Future",
        "past": "Past",
        "unknown": "Unknown",
    }

    def map_urgency(self, raw_urgency: Optional[str]) -> Tuple[UrgencyType, Optional[str]]:
        """Map raw urgency string to canonical UrgencyType.

        Args:
            raw_urgency: Raw urgency string from ParsedAlert.

        Returns:
            Tuple[UrgencyType, Optional[str]]: Canonical urgency enum and an optional parse warning if unknown.
        """
        if not raw_urgency or not raw_urgency.strip():
            return "Unknown", "Missing raw urgency; mapped to 'Unknown'"

        cleaned = raw_urgency.strip().lower()

        if cleaned in self._CANONICAL_LOOKUP:
            return self._CANONICAL_LOOKUP[cleaned], None

        warning = f"Unknown urgency term '{raw_urgency}'; mapped to 'Unknown'"
        logger.info(warning)
        return "Unknown", warning
