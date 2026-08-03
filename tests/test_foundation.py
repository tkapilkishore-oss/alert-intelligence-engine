"""Infrastructure verification tests for Stage 1 Foundation."""

import logging
import pytest
from src.constants import SUPPORTED_SOURCE_FORMATS
from src.logger import get_logger
from src.parsers.base_parser import BaseParser
from src.pipeline import Pipeline
from src.schema import NormalizedAlert, ParsedAlert
from src.utils.datetime_utils import normalize_datetime
from src.utils.text_utils import clean_text, normalize_whitespace


def test_package_imports() -> None:
    """Verify that all core project modules import successfully."""
    assert Pipeline is not None
    assert BaseParser is not None
    assert ParsedAlert is not None
    assert NormalizedAlert is not None
    assert SUPPORTED_SOURCE_FORMATS == ("json", "cap_xml", "rss", "plaintext")


def test_base_parser_is_abstract() -> None:
    """Verify that BaseParser cannot be instantiated directly without subclassing."""
    with pytest.raises(TypeError):
        BaseParser()  # type: ignore[abstract]


def test_parsed_alert_instantiation() -> None:
    """Verify that ParsedAlert Pydantic model instantiates correctly with required fields."""
    parsed = ParsedAlert(
        source="test_source",
        source_format="json",
        raw_hazard="flooding",
        raw_severity="high",
    )
    assert parsed.source == "test_source"
    assert parsed.source_format == "json"
    assert parsed.raw_hazard == "flooding"
    assert parsed.parse_warnings == []


def test_normalized_alert_instantiation() -> None:
    """Verify that NormalizedAlert Pydantic model instantiates correctly matching schema."""
    normalized = NormalizedAlert(
        alert_id="ALT-001",
        source="test_source",
        hazard_type="flood",
        severity="Severe",
        urgency="Immediate",
        certainty="Observed",
        location_name="Test City",
        recommended_action="Evacuate",
        source_format="json",
    )
    assert normalized.alert_id == "ALT-001"
    assert normalized.hazard_type == "flood"
    assert normalized.severity == "Severe"
    assert normalized.is_duplicate is False


def test_logger_initialization() -> None:
    """Verify that project logger initializes with correct configuration and level."""
    logger = get_logger("test_logger", level="INFO")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO


def test_utility_skeletons_exist() -> None:
    """Verify utility function skeletons exist and raise NotImplementedError on call."""
    with pytest.raises(NotImplementedError):
        normalize_datetime("2026-08-03T00:00:00Z")

    with pytest.raises(NotImplementedError):
        clean_text("sample")

    with pytest.raises(NotImplementedError):
        normalize_whitespace("sample text")
