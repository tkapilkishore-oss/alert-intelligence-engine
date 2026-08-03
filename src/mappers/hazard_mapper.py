"""Hazard Mapper module for Stage 7 Normalization Engine."""

from typing import Optional, Tuple
from src.logger import get_logger
from src.schema import HazardType

logger = get_logger(__name__)


class HazardMapper:
    """Mapper responsible for deterministically classifying raw hazard strings into canonical HazardTypes."""

    # Deterministic mapping lookup table (lowercase matching)
    HAZARD_PATTERNS: tuple[tuple[tuple[str, ...], HazardType], ...] = (
        (("urban flood", "flood warning", "flood watch", "flash flood", "flood"), "flood"),
        (("heat wave", "heatwave", "heat stress", "extreme heat"), "heatwave"),
        (("cyclone wind", "cyclone", "tropical storm", "typhoon", "hurricane"), "cyclone"),
        (("landslide", "mudslide"), "landslide"),
        (("lightning", "thunderstorm"), "lightning"),
        (("earthquake", "seismic activity"), "earthquake"),
    )

    def map_hazard(self, raw_hazard: Optional[str]) -> Tuple[HazardType, Optional[str]]:
        """Map raw hazard description to canonical HazardType deterministically.

        Args:
            raw_hazard: Raw hazard string from ParsedAlert.

        Returns:
            Tuple[HazardType, Optional[str]]: Canonical hazard enum and an optional parse warning if unclassified.
        """
        if not raw_hazard or not raw_hazard.strip():
            return "other", "Missing raw hazard; mapped to 'other'"

        cleaned = raw_hazard.strip().lower()

        for keywords, canonical in self.HAZARD_PATTERNS:
            for kw in keywords:
                if kw in cleaned:
                    return canonical, None

        logger.info(f"Unmapped hazard '{raw_hazard}' deterministically mapped to 'other'")
        return "other", f"Unrecognized hazard term '{raw_hazard}'; mapped to 'other'"
