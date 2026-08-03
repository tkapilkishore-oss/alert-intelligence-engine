"""Datetime utility functions for Alert Intelligence Engine."""

from typing import Optional
from src.mappers.datetime_mapper import DatetimeMapper

_mapper_instance = DatetimeMapper()


def normalize_datetime(raw_datetime: Optional[str]) -> Optional[str]:
    """Convert raw datetime string into standard ISO-8601 string or None.

    Args:
        raw_datetime: Raw date/time string from source input.

    Returns:
        Optional[str]: Standardized ISO-8601 formatted datetime string or None.
    """
    iso_str, _ = _mapper_instance.map_datetime(raw_datetime)
    return iso_str
