"""Certainty Mapper module for Stage 7 Normalization Engine."""

from typing import Dict, Optional, Tuple
from src.logger import get_logger
from src.schema import CertaintyType

logger = get_logger(__name__)


class CertaintyMapper:
    """Mapper responsible for mapping raw certainty strings to canonical CertaintyType."""

    _CANONICAL_LOOKUP: Dict[str, CertaintyType] = {
        "observed": "Observed",
        "likely": "Likely",
        "possible": "Possible",
        "unknown": "Unknown",
    }

    def map_certainty(self, raw_certainty: Optional[str]) -> Tuple[CertaintyType, Optional[str]]:
        """Map raw certainty string to canonical CertaintyType.

        Args:
            raw_certainty: Raw certainty string from ParsedAlert.

        Returns:
            Tuple[CertaintyType, Optional[str]]: Canonical certainty enum and an optional parse warning if unknown.
        """
        if not raw_certainty or not raw_certainty.strip():
            return "Unknown", "Missing raw certainty; mapped to 'Unknown'"

        cleaned = raw_certainty.strip().lower()

        if cleaned in self._CANONICAL_LOOKUP:
            return self._CANONICAL_LOOKUP[cleaned], None

        warning = f"Unknown certainty term '{raw_certainty}'; mapped to 'Unknown'"
        logger.info(warning)
        return "Unknown", warning
