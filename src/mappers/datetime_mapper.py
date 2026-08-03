"""Datetime Mapper module for Stage 7 Normalization Engine."""

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional, Tuple
from src.logger import get_logger

logger = get_logger(__name__)


class DatetimeMapper:
    """Mapper responsible for deterministically normalizing supported input datetime strings into ISO-8601 format."""

    _EXPLICIT_STRPTIME_FORMATS: tuple[str, ...] = (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d %b %Y %H:%M",
        "%d %b %Y %H:%M:%S",
    )

    def map_datetime(self, raw_datetime: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Normalize raw datetime string into standard ISO-8601 string without throwing exceptions.

        Args:
            raw_datetime: Raw date/time string from source input.

        Returns:
            Tuple[Optional[str], Optional[str]]: Standardized ISO-8601 string and an optional parse warning if conversion fails.
        """
        if not raw_datetime or not str(raw_datetime).strip():
            return None, None

        cleaned = str(raw_datetime).strip()

        # 1. Try ISO-8601 format directly
        try:
            dt = datetime.fromisoformat(cleaned)
            return dt.isoformat(), None
        except (ValueError, TypeError):
            pass

        # 2. Try RFC 2822 / RSS feed format (e.g. Thu, 17 Jul 2025 12:00:00 +0530)
        try:
            dt = parsedate_to_datetime(cleaned)
            if dt is not None:
                return dt.isoformat(), None
        except Exception:
            pass

        # 3. Try deterministic explicit strptime patterns
        for fmt in self._EXPLICIT_STRPTIME_FORMATS:
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.isoformat(), None
            except (ValueError, TypeError):
                continue

        warning = f"Failed to normalize invalid datetime string '{raw_datetime}'"
        logger.info(warning)
        return None, warning
