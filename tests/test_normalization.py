"""Integration unit tests for NormalizationEngine and ParsedAlert to NormalizedAlert conversion."""

import pytest
from src.normalization import NormalizationEngine
from src.schema import NormalizedAlert, ParsedAlert


def test_normalization_engine_complete_conversion() -> None:
    engine = NormalizationEngine()

    parsed = ParsedAlert(
        raw_hazard="Urban Flood",
        raw_severity="Orange",
        raw_urgency="Immediate",
        raw_certainty="Observed",
        raw_location="Devapur Block 2",
        raw_start_time="2025-07-17 03:00",
        raw_end_time="2025-07-18 15:00",
        raw_action="Avoid low-lying roads and move valuables above ground level.",
        source="Demo IMD Feed",
        source_format="json",
        raw_payload={"id": "JSON-001"},
        parse_warnings=["parser warning 1"],
    )

    normalized = engine.normalize(parsed)

    assert isinstance(normalized, NormalizedAlert)
    assert normalized.alert_id == "JSON-001"
    assert normalized.source == "Demo IMD Feed"
    assert normalized.hazard_type == "flood"
    assert normalized.severity == "Severe"
    assert normalized.urgency == "Immediate"
    assert normalized.certainty == "Observed"
    assert normalized.location_name == "Devapur Block 2"
    assert normalized.location_id == "BLK-03-2"
    assert normalized.start_time == "2025-07-17T03:00:00"
    assert normalized.end_time == "2025-07-18T15:00:00"
    assert normalized.recommended_action == "Avoid low-lying roads and move valuables above ground level."
    assert normalized.source_format == "json"
    assert normalized.is_duplicate is False
    assert "parser warning 1" in normalized.parse_warnings


def test_normalization_engine_immutability() -> None:
    engine = NormalizationEngine()

    parsed = ParsedAlert(
        raw_hazard="Heat Wave",
        raw_severity="Red",
        raw_location="Nirmala",
        source="State EOC Demo",
        source_format="plaintext",
        parse_warnings=["initial warning"],
    )

    original_warnings_len = len(parsed.parse_warnings)
    original_hazard = parsed.raw_hazard

    normalized = engine.normalize(parsed)

    # Verify input parsed alert is NOT mutated
    assert parsed.raw_hazard == original_hazard
    assert len(parsed.parse_warnings) == original_warnings_len
    assert parsed is not normalized  # Different object references


def test_normalization_engine_unknown_location_and_invalid_datetime() -> None:
    engine = NormalizationEngine()

    parsed = ParsedAlert(
        raw_hazard="Unknown hazard event",
        raw_severity="invalid_sev",
        raw_urgency="invalid_urg",
        raw_certainty="invalid_cert",
        raw_location="Unknown City X",
        raw_start_time="bad datetime string",
        source="Test Source",
        source_format="plaintext",
    )

    normalized = engine.normalize(parsed)

    assert normalized.hazard_type == "other"
    assert normalized.severity == "Unknown"
    assert normalized.urgency == "Unknown"
    assert normalized.certainty == "Unknown"
    assert normalized.location_name == "Unknown City X"
    assert normalized.location_id is None
    assert normalized.start_time is None
    assert len(normalized.parse_warnings) > 0
