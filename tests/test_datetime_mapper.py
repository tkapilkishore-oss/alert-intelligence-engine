"""Unit tests for DatetimeMapper."""

import pytest
from src.mappers.datetime_mapper import DatetimeMapper


def test_datetime_mapper_dataset_formats() -> None:
    mapper = DatetimeMapper()

    # Format 1: YYYY-MM-DD HH:MM
    dt_str, warn = mapper.map_datetime("2025-07-17 03:00")
    assert dt_str == "2025-07-17T03:00:00"
    assert warn is None

    # Format 2: ISO-8601 string
    dt_str, warn = mapper.map_datetime("2025-07-18T21:00:00+05:30")
    assert dt_str == "2025-07-18T21:00:00+05:30"
    assert warn is None

    # Format 3: RFC 2822 RSS date
    dt_str, warn = mapper.map_datetime("Thu, 17 Jul 2025 12:00:00 +0530")
    assert dt_str is not None
    assert "2025-07-17" in dt_str
    assert warn is None

    # Format 4: DD MMM YYYY HH:MM
    dt_str, warn = mapper.map_datetime("15 Jul 2025 18:00")
    assert dt_str == "2025-07-15T18:00:00"
    assert warn is None


def test_datetime_mapper_malformed_datetime() -> None:
    mapper = DatetimeMapper()
    dt_str, warn = mapper.map_datetime("invalid date string")
    assert dt_str is None
    assert warn is not None
    assert "Failed to normalize invalid datetime string" in warn


def test_datetime_mapper_none_input() -> None:
    mapper = DatetimeMapper()
    dt_str, warn = mapper.map_datetime(None)
    assert dt_str is None
    assert warn is None
