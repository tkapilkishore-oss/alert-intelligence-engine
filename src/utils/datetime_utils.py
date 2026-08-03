"""Datetime utility function skeletons."""

from typing import Optional


def normalize_datetime(raw_datetime: Optional[str]) -> Optional[str]:
    """Convert raw datetime string into standard ISO-8601 string or None.

    Args:
        raw_datetime: Raw date/time string from source input.

    Returns:
        Optional[str]: Standardized ISO-8601 formatted datetime string or None.
    """
    # TODO: Stage 7 — Implement datetime parsing and ISO-8601 normalization
    raise NotImplementedError("Datetime normalization will be implemented in Stage 7.")
