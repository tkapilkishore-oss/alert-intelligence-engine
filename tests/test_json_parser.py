"""Tests for JsonParser implementation."""

import copy
import json
from pathlib import Path
import pytest

from src.parsers.base_parser import BaseParser
from src.parsers.json_parser import JsonParser
from src.schema import ParsedAlert

DATA_FILE = Path(__file__).parent.parent / "data" / "raw_alerts_json.json"


def test_json_parser_imports_and_inheritance():
    """Verify JsonParser imports correctly and inherits from BaseParser."""
    parser = JsonParser()
    assert isinstance(parser, BaseParser)
    assert issubclass(JsonParser, BaseParser)


def test_json_parser_dataset_loading():
    """Verify JsonParser loads and parses the assignment dataset successfully."""
    assert DATA_FILE.exists(), f"Dataset file missing at {DATA_FILE}"
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    parser = JsonParser()
    alerts = parser.parse(raw_data)

    assert isinstance(alerts, list)
    assert len(alerts) == 14
    for alert in alerts:
        assert isinstance(alert, ParsedAlert)
        assert alert.source_format == "json"
        assert alert.source != ""
        assert isinstance(alert.raw_payload, dict)


def test_json_parser_field_alias_resolution():
    """Verify JsonParser correctly extracts all field aliases present in raw_alerts_json.json."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    parser = JsonParser()
    alerts = parser.parse(raw_data)
    alerts_by_id = {
        alert.raw_payload.get("id") or alert.raw_payload.get("identifier") or alert.raw_payload.get("alertCode"): alert
        for alert in alerts
    }

    # JSON-001: event, area, severity, valid_from, valid_to, advice
    rec1 = alerts_by_id["JSON-001"]
    assert rec1.raw_hazard == "Urban Flood"
    assert rec1.raw_location == "Nirmala"
    assert rec1.raw_severity == "Moderate"
    assert rec1.raw_start_time == "2025-07-17 03:00"
    assert rec1.raw_end_time == "2025-07-18 15:00"
    assert rec1.raw_action == "Avoid low-lying roads and move valuables above ground level."
    assert rec1.source == "Demo IMD Feed"

    # JSON-003: warningType, district, startTime, endTime, recommended_action
    rec3 = alerts_by_id["JSON-003"]
    assert rec3.raw_hazard == "Lightning"
    assert rec3.raw_location == "Kalyanpur"
    assert rec3.raw_start_time == "2025-07-17 17:00"
    assert rec3.raw_end_time == "2025-07-19 05:00"
    assert rec3.raw_action == "Stay indoors and avoid open fields or isolated trees."

    # JSON-004: hazard, severity_text, expires
    rec4 = alerts_by_id["JSON-004"]
    assert rec4.raw_hazard == "Heat Wave"
    assert rec4.raw_severity == "Red"
    assert rec4.raw_end_time == "2025-07-16 08:00"
    assert rec4.source == "State EOC Demo"

    # JSON-005 (first occurrence): alertCode, hazard, location, level, onset, instruction
    rec5 = alerts_by_id["JSON-005"]
    assert rec5.raw_hazard in ["Urban Flood", "Landslide"]  # Two JSON-005 records present in dataset
    assert rec5.raw_severity in ["Red", "Orange"]


def test_json_parser_input_types():
    """Verify JsonParser supports dict, list of dicts, and JSON string inputs."""
    parser = JsonParser()
    sample_record = {
        "event": "Cyclone",
        "area": "Coastal Zone",
        "severity": "Severe",
        "source": "Test Source",
    }

    # Dict input
    alerts_dict = parser.parse(sample_record)
    assert len(alerts_dict) == 1
    assert alerts_dict[0].raw_hazard == "Cyclone"

    # List of dicts input
    alerts_list = parser.parse([sample_record])
    assert len(alerts_list) == 1
    assert alerts_list[0].raw_hazard == "Cyclone"

    # JSON string input
    json_str = json.dumps([sample_record])
    alerts_str = parser.parse(json_str)
    assert len(alerts_str) == 1
    assert alerts_str[0].raw_hazard == "Cyclone"


def test_json_parser_malformed_input_resilience():
    """Verify JsonParser handles malformed elements without crashing."""
    parser = JsonParser()
    mixed_input = [
        {"event": "Flood", "area": "Zone A", "severity": "Moderate"},
        "invalid_string_record",
        12345,
        None,
        {"event": "Landslide", "area": "Zone B", "severity": "High"},
    ]

    alerts = parser.parse(mixed_input)
    assert len(alerts) == 2
    assert alerts[0].raw_hazard == "Flood"
    assert alerts[1].raw_hazard == "Landslide"

    # Invalid JSON string
    invalid_str_alerts = parser.parse("{invalid_json: true,")
    assert invalid_str_alerts == []


def test_json_parser_input_immutability():
    """Verify JsonParser is read-only and does not mutate the original input structure."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    raw_data_copy = copy.deepcopy(raw_data)
    parser = JsonParser()

    _ = parser.parse(raw_data)

    assert raw_data == raw_data_copy, "JsonParser modified the original input object!"
