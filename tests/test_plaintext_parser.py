"""Automated test suite for Plaintext Alert Parser."""

from pathlib import Path
import pytest

from src.parsers.base_parser import BaseParser
from src.parsers.plaintext_parser import PlaintextParser
from src.schema import ParsedAlert

PLAINTEXT_DATASET_PATH = Path("data/raw_alerts_plaintext.txt")


def test_plaintext_parser_imports_and_inheritance():
    """Verify PlaintextParser imports correctly and inherits from BaseParser."""
    parser = PlaintextParser()
    assert isinstance(parser, BaseParser)
    assert hasattr(parser, "parse")


def test_plaintext_parser_dataset_loading():
    """Verify parsing data/raw_alerts_plaintext.txt extracts exactly 9 ParsedAlert objects."""
    parser = PlaintextParser()
    raw_text = PLAINTEXT_DATASET_PATH.read_text(encoding="utf-8")
    alerts = parser.parse(raw_text)

    assert isinstance(alerts, list)
    assert len(alerts) == 9
    assert all(isinstance(a, ParsedAlert) for a in alerts)


def test_plaintext_parser_parsed_alert_baseline_contract():
    """Verify every ParsedAlert produced satisfies baseline attributes:

    - source_format == 'plaintext'
    - parse_warnings initialized as a list
    - raw_payload populated with original_text and detected_pattern
    """
    parser = PlaintextParser()
    raw_text = PLAINTEXT_DATASET_PATH.read_text(encoding="utf-8")
    alerts = parser.parse(raw_text)

    assert len(alerts) == 9
    for alert in alerts:
        assert alert.source_format == "plaintext"
        assert isinstance(alert.parse_warnings, list)
        assert isinstance(alert.raw_payload, dict)
        assert "original_text" in alert.raw_payload
        assert len(alert.raw_payload["original_text"]) > 0
        assert "detected_pattern" in alert.raw_payload


def test_plaintext_parser_field_extraction():
    """Verify field extraction accuracy for representative plaintext alerts."""
    parser = PlaintextParser()
    raw_text = PLAINTEXT_DATASET_PATH.read_text(encoding="utf-8")
    alerts = parser.parse(raw_text)

    # PT-001: ALERT PT-001 | Devapur | Severe flood warning | starts 2025-07-16 08:00 | avoid river-side roads
    pt_001 = alerts[0]
    assert pt_001.raw_location == "Devapur"
    assert pt_001.raw_severity == "Severe"
    assert "flood" in pt_001.raw_hazard.lower()
    assert pt_001.raw_start_time == "starts 2025-07-16 08:00"
    assert pt_001.raw_action == "avoid river-side roads"

    # PT-002: PT-002 Suryanagar Block 2: HEATWAVE ORANGE advisory valid tomorrow afternoon. Set up water points.
    pt_002 = alerts[1]
    assert pt_002.raw_location == "Suryanagar Block 2"
    assert pt_002.raw_severity == "ORANGE"
    assert "HEATWAVE" in pt_002.raw_hazard
    assert pt_002.raw_action == "Set up water points."

    # PT-003 / District Control: District Control: RED lightning alert for Vanasthal from 15 Jul 2025 18:00 to 15 Jul 2025 22:00. Stay indoors.
    pt_003 = alerts[2]
    assert pt_003.source == "District Control"
    assert pt_003.raw_severity == "RED"
    assert pt_003.raw_hazard == "lightning"
    assert pt_003.raw_location == "Vanasthal"
    assert pt_003.raw_start_time == "15 Jul 2025 18:00"
    assert pt_003.raw_end_time == "15 Jul 2025 22:00"
    assert pt_003.raw_action == "Stay indoors."

    # PT-004: PT-004 | Port Lakshmi | Cyclone Wind | HIGH | fishermen advised not to venture into sea
    pt_004 = alerts[3]
    assert pt_004.raw_location == "Port Lakshmi"
    assert pt_004.raw_hazard == "Cyclone Wind"
    assert pt_004.raw_severity == "HIGH"
    assert pt_004.raw_action == "fishermen advised not to venture into sea"


def test_plaintext_parser_malformed_and_missing_fields():
    """Verify malformed record handling and explicit parse_warnings generation."""
    parser = PlaintextParser()
    raw_text = PLAINTEXT_DATASET_PATH.read_text(encoding="utf-8")
    alerts = parser.parse(raw_text)

    # Line 5: Malformed alert: heavy rain maybe somewhere soon
    malformed_alert = alerts[4]
    assert malformed_alert.raw_hazard == "heavy rain"
    assert malformed_alert.raw_severity is None
    assert malformed_alert.raw_location is None
    assert "missing severity" in malformed_alert.parse_warnings
    assert "missing location" in malformed_alert.parse_warnings
    assert "missing start_time" in malformed_alert.parse_warnings


def test_plaintext_parser_input_types():
    """Verify PlaintextParser accepts str, bytes, and List[str]."""
    parser = PlaintextParser()
    raw_str = PLAINTEXT_DATASET_PATH.read_text(encoding="utf-8")
    raw_bytes = raw_str.encode("utf-8")
    raw_list = [line for line in raw_str.splitlines() if line.strip()]

    res_str = parser.parse(raw_str)
    res_bytes = parser.parse(raw_bytes)
    res_list = parser.parse(raw_list)

    assert len(res_str) == 9
    assert len(res_bytes) == 9
    assert len(res_list) == 9


def test_plaintext_parser_malformed_input_resilience():
    """Verify graceful handling for invalid or empty inputs."""
    parser = PlaintextParser()

    assert parser.parse("") == []
    assert parser.parse(12345) == []
    assert parser.parse(None) == []


def test_plaintext_parser_input_immutability():
    """Verify input list or string remains unmutated after parsing."""
    parser = PlaintextParser()
    raw_list = ["ALERT PT-001 | Devapur | Severe flood warning | starts 2025-07-16 08:00 | avoid river-side roads"]
    copy_list = list(raw_list)

    _ = parser.parse(raw_list)
    assert raw_list == copy_list
