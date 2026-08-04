"""Unit test suite for Stage 10 AlertPipeline orchestration engine."""

import json
import pytest
from src.parsers.cap_parser import CapParser
from src.parsers.json_parser import JsonParser
from src.parsers.plaintext_parser import PlaintextParser
from src.parsers.rss_parser import RssParser
from src.pipeline import AlertPipeline, Pipeline
from src.schema import NormalizedAlert, ParsedAlert


def test_pipeline_backward_compatibility() -> None:
    """Verify that Pipeline is an alias of AlertPipeline."""
    assert Pipeline is AlertPipeline
    pipeline = Pipeline()
    assert isinstance(pipeline, AlertPipeline)


def test_parser_selection() -> None:
    """Verify that _get_parser selects the correct BaseParser implementation."""
    pipeline = AlertPipeline()
    assert isinstance(pipeline._get_parser("json"), JsonParser)
    assert isinstance(pipeline._get_parser("cap_xml"), CapParser)
    assert isinstance(pipeline._get_parser("rss"), RssParser)
    assert isinstance(pipeline._get_parser("plaintext"), PlaintextParser)
    assert isinstance(pipeline._get_parser(" JSON "), JsonParser)


def test_unsupported_source_format() -> None:
    """Verify that unsupported source formats raise descriptive ValueError."""
    pipeline = AlertPipeline()
    with pytest.raises(ValueError, match="Unsupported source format: 'yaml'"):
        pipeline.process([], "yaml")

    with pytest.raises(ValueError, match="Invalid source format"):
        pipeline.process([], "")  # type: ignore[arg-type]


def test_empty_dataset() -> None:
    """Verify that empty inputs return an empty list without errors."""
    pipeline = AlertPipeline()
    assert pipeline.process([], "json") == []
    assert pipeline.process("", "cap_xml") == []
    assert pipeline.process(None, "rss") == []


def test_json_pipeline() -> None:
    """Verify end-to-end JSON pipeline processing."""
    raw_data = [
        {
            "id": "JSON-TEST-001",
            "event": "Urban Flood",
            "area": "Nirmala",
            "severity": "Moderate",
            "urgency": "Future",
            "certainty": "Likely",
            "valid_from": "2025-07-17 03:00",
            "valid_to": "2025-07-18 15:00",
            "advice": "Avoid low-lying roads.",
            "source": "Test Feed",
        }
    ]
    pipeline = AlertPipeline()
    results = pipeline.process(raw_data, "json")

    assert len(results) == 1
    alert = results[0]
    assert isinstance(alert, NormalizedAlert)
    assert alert.alert_id == "JSON-TEST-001"
    assert alert.hazard_type == "flood"
    assert alert.severity == "Moderate"
    assert alert.urgency == "Future"
    assert alert.certainty == "Likely"
    assert alert.location_name == "Nirmala"
    assert alert.recommended_action == "Avoid low-lying roads."
    assert alert.is_duplicate is False


def test_cap_xml_pipeline() -> None:
    """Verify end-to-end CAP XML pipeline processing."""
    raw_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
        <identifier>CAP-TEST-001</identifier>
        <sender>State EOC</sender>
        <info>
            <event>Cyclone</event>
            <severity>Severe</severity>
            <urgency>Immediate</urgency>
            <certainty>Observed</certainty>
            <area>
                <areaDesc>Port Lakshmi</areaDesc>
            </area>
            <instruction>Evacuate coastal area.</instruction>
        </info>
    </alert>"""

    pipeline = AlertPipeline()
    results = pipeline.process(raw_xml, "cap_xml")

    assert len(results) == 1
    alert = results[0]
    assert isinstance(alert, NormalizedAlert)
    assert alert.hazard_type == "cyclone"
    assert alert.severity == "Severe"
    assert alert.urgency == "Immediate"
    assert alert.certainty == "Observed"
    assert alert.location_name == "Port Lakshmi"
    assert alert.recommended_action == "Evacuate coastal area."


def test_rss_pipeline() -> None:
    """Verify end-to-end RSS XML pipeline processing."""
    raw_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Disaster Feed</title>
            <item>
                <guid>RSS-TEST-001</guid>
                <title>Severe: Heatwave Warning for Devapur</title>
                <description>Action: Avoid direct sunlight during noon hours.</description>
                <pubDate>Thu, 17 Jul 2025 08:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>"""

    pipeline = AlertPipeline()
    results = pipeline.process(raw_rss, "rss")

    assert len(results) == 1
    alert = results[0]
    assert isinstance(alert, NormalizedAlert)
    assert alert.hazard_type == "heatwave"
    assert alert.severity == "Severe"
    assert alert.location_name == "Devapur"
    assert alert.recommended_action == "Avoid direct sunlight during noon hours"


def test_plaintext_pipeline() -> None:
    """Verify end-to-end Plaintext pipeline processing."""
    raw_text = "ALERT PT-001 | Devapur | Severe flood warning | valid_from 2025-07-17 | Move to high ground immediately."

    pipeline = AlertPipeline()
    results = pipeline.process(raw_text, "plaintext")

    assert len(results) == 1
    alert = results[0]
    assert isinstance(alert, NormalizedAlert)
    assert alert.hazard_type == "flood"
    assert alert.severity == "Severe"
    assert alert.location_name == "Devapur"
    assert alert.recommended_action == "Move to high ground immediately."


def test_structural_validation_integration() -> None:
    """Verify that structurally invalid records are filtered out."""
    pipeline = AlertPipeline()
    empty_alert = ParsedAlert(source="empty_source", source_format="json", raw_payload={})
    results = pipeline._validate_parsed([empty_alert])
    assert len(results) == 0


def test_normalization_integration() -> None:
    """Verify normalization helper maps raw fields correctly."""
    pipeline = AlertPipeline()
    parsed = ParsedAlert(
        raw_hazard="urban flooding",
        raw_severity="high",
        raw_location="kalyanpur block 1",
        raw_action="seek shelter",
        source="unit_test",
        source_format="json",
    )
    normalized_list = pipeline._normalize([parsed])
    assert len(normalized_list) == 1
    norm = normalized_list[0]
    assert norm.hazard_type == "flood"
    assert norm.severity == "Severe"
    assert norm.location_id == "BLK-04-1"


def test_schema_validation_integration() -> None:
    """Verify schema validation helper filters invalid normalized records."""
    pipeline = AlertPipeline()
    invalid_norm = NormalizedAlert(
        alert_id="",  # empty alert_id makes it invalid
        source="test",
        hazard_type="flood",
        severity="Severe",
        urgency="Immediate",
        certainty="Observed",
        location_name="Test Loc",
        recommended_action="Act",
        source_format="json",
    )
    validated = pipeline._validate_normalized([invalid_norm])
    assert len(validated) == 0


def test_deduplication_integration() -> None:
    """Verify deduplication engine flags duplicate alerts in batch."""
    pipeline = AlertPipeline()
    raw_data = [
        {
            "id": "JSON-001",
            "event": "Heat Wave",
            "area": "Devapur",
            "severity": "Red",
            "urgency": "Expected",
            "certainty": "Observed",
            "startTime": "2025-07-18 03:00",
            "expires": "2025-07-19 03:00",
            "recommended_action": "Avoid outdoor work between 12:00 and 15:00.",
            "source": "Feed A",
        },
        {
            "id": "JSON-002",
            "event": "Heat Wave",
            "area": "Devapur",
            "severity": "Red",
            "urgency": "Expected",
            "certainty": "Observed",
            "startTime": "2025-07-18 03:00",
            "expires": "2025-07-19 03:00",
            "recommended_action": "Avoid outdoor work between 12:00 and 15:00.",
            "source": "Feed B",
        },
    ]

    results = pipeline.process(raw_data, "json")
    assert len(results) == 2
    assert results[0].is_duplicate is False
    assert results[1].is_duplicate is True


def test_end_to_end_data_regression() -> None:
    """Verify complete pipeline execution on provided dataset files."""
    pipeline = AlertPipeline()

    # 1. JSON dataset
    with open("data/raw_alerts_json.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    json_results = pipeline.process(json_data, "json")
    assert len(json_results) > 0
    assert all(isinstance(a, NormalizedAlert) for a in json_results)

    # 2. CAP XML dataset
    with open("data/raw_alerts_cap.xml", "r", encoding="utf-8") as f:
        cap_data = f.read()
    cap_results = pipeline.process(cap_data, "cap_xml")
    assert len(cap_results) > 0
    assert all(isinstance(a, NormalizedAlert) for a in cap_results)

    # 3. RSS XML dataset
    with open("data/raw_alerts_rss.xml", "r", encoding="utf-8") as f:
        rss_data = f.read()
    rss_results = pipeline.process(rss_data, "rss")
    assert len(rss_results) > 0
    assert all(isinstance(a, NormalizedAlert) for a in rss_results)

    # 4. Plaintext dataset
    with open("data/raw_alerts_plaintext.txt", "r", encoding="utf-8") as f:
        pt_data = f.read()
    pt_results = pipeline.process(pt_data, "plaintext")
    assert len(pt_results) > 0
    assert all(isinstance(a, NormalizedAlert) for a in pt_results)


def test_input_immutability() -> None:
    """Verify that raw input dictionary/list is not mutated during processing."""
    pipeline = AlertPipeline()
    original_item = {
        "id": "IMMUTABLE-001",
        "event": "Flood",
        "area": "Nirmala",
        "severity": "Moderate",
        "advice": "Move up.",
    }
    input_data = [dict(original_item)]
    input_data_copy = [dict(original_item)]

    _ = pipeline.process(input_data, "json")
    assert input_data == input_data_copy
