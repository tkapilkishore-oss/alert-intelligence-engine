"""Automated test suite for RSS XML Alert Parser."""

from pathlib import Path
import xml.etree.ElementTree as ET
import pytest

from src.parsers.base_parser import BaseParser
from src.parsers.rss_parser import RssParser
from src.schema import ParsedAlert

RSS_DATASET_PATH = Path("data/raw_alerts_rss.xml")


def test_rss_parser_imports_and_inheritance():
    """Verify RssParser imports correctly and inherits from BaseParser."""
    parser = RssParser()
    assert isinstance(parser, BaseParser)
    assert hasattr(parser, "parse")


def test_rss_parser_dataset_loading():
    """Verify parsing data/raw_alerts_rss.xml extracts exactly 10 ParsedAlert objects."""
    parser = RssParser()
    raw_xml = RSS_DATASET_PATH.read_text(encoding="utf-8")
    alerts = parser.parse(raw_xml)

    assert isinstance(alerts, list)
    assert len(alerts) == 10
    assert all(isinstance(a, ParsedAlert) for a in alerts)


def test_rss_parser_parsed_alert_baseline_contract():
    """Verify every ParsedAlert produced satisfies baseline attributes:

    - source_format == 'rss'
    - parse_warnings initialized as a list
    - raw_payload populated
    """
    parser = RssParser()
    raw_xml = RSS_DATASET_PATH.read_text(encoding="utf-8")
    alerts = parser.parse(raw_xml)

    assert len(alerts) == 10
    for alert in alerts:
        assert alert.source_format == "rss"
        assert isinstance(alert.parse_warnings, list)
        assert isinstance(alert.raw_payload, dict)
        assert len(alert.raw_payload) > 0
        assert "guid" in alert.raw_payload
        assert "title" in alert.raw_payload


def test_rss_parser_field_extraction():
    """Verify correct field extraction for representative RSS items."""
    parser = RssParser()
    raw_xml = RSS_DATASET_PATH.read_text(encoding="utf-8")
    alerts = parser.parse(raw_xml)

    # RSS-001: RED ALERT: Urban Flood warning for Suryanagar Block 3
    rss_001 = next(a for a in alerts if a.raw_payload.get("guid") == "RSS-001")
    assert rss_001.raw_severity == "RED ALERT"
    assert rss_001.raw_hazard == "Urban Flood"
    assert rss_001.raw_location == "Suryanagar Block 3"
    assert rss_001.raw_action == "Avoid low-lying roads and move valuables above ground level"
    assert rss_001.raw_start_time == "Thu, 17 Jul 2025 12:00:00 +0530"
    assert rss_001.source == "Demo Disaster Alert Feed"

    # RSS-003: Yellow: Lightning warning for Suryanagar Block 3
    rss_003 = next(a for a in alerts if a.raw_payload.get("guid") == "RSS-003")
    assert rss_003.raw_severity == "Yellow"
    assert rss_003.raw_hazard == "Lightning"
    assert rss_003.raw_location == "Suryanagar Block 3"

    # RSS-004: Orange: Landslide warning for Suryanagar Block 2
    rss_004 = next(a for a in alerts if a.raw_payload.get("guid") == "RSS-004")
    assert rss_004.raw_severity == "Orange"
    assert rss_004.raw_hazard == "Landslide"

    # RSS-005: Advisory: Lightning warning for Vanasthal Block 2
    rss_005 = next(a for a in alerts if a.raw_payload.get("guid") == "RSS-005")
    assert rss_005.raw_severity == "Advisory"
    assert rss_005.raw_hazard == "Lightning"
    assert rss_005.raw_location == "Vanasthal Block 2"


def test_rss_parser_input_types():
    """Verify RssParser accepts str, bytes, ET.ElementTree, ET.Element, and List[ET.Element]."""
    parser = RssParser()
    raw_str = RSS_DATASET_PATH.read_text(encoding="utf-8")
    raw_bytes = raw_str.encode("utf-8")
    elem_tree = ET.parse(RSS_DATASET_PATH)
    root_elem = elem_tree.getroot()
    item_elems = root_elem.findall(".//item")

    res_str = parser.parse(raw_str)
    res_bytes = parser.parse(raw_bytes)
    res_tree = parser.parse(elem_tree)
    res_elem = parser.parse(root_elem)
    res_list = parser.parse(item_elems)

    assert len(res_str) == 10
    assert len(res_bytes) == 10
    assert len(res_tree) == 10
    assert len(res_elem) == 10
    assert len(res_list) == 10


def test_rss_parser_malformed_input_resilience():
    """Verify graceful handling for invalid XML and non-XML inputs."""
    parser = RssParser()

    assert parser.parse("<rss><channel><item>unclosed tag</rss>") == []
    assert parser.parse("Not XML content") == []
    assert parser.parse(12345) == []
    assert parser.parse(None) == []


def test_rss_parser_single_malformed_record_resilience():
    """Verify single malformed item logs warning and skips while valid items parse cleanly."""
    parser = RssParser()
    xml_with_bad_item = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Mixed Feed</title>
        <item>
          <title>RED ALERT: Urban Flood warning for Suryanagar Block 3</title>
          <description>Urban Flood expected in Suryanagar Block 3. Action: Evacuate area.</description>
          <pubDate>Thu, 17 Jul 2025 12:00:00 +0530</pubDate>
          <guid>RSS-001</guid>
        </item>
        <item>BROKEN ITEM NODE CONTENT THAT CAUSES EXCEPTION</item>
        <item>
          <title>Yellow: Lightning warning for Suryanagar Block 3</title>
          <description>Lightning expected in Suryanagar Block 3.</description>
          <pubDate>Tue, 15 Jul 2025 14:00:00 +0530</pubDate>
          <guid>RSS-003</guid>
        </item>
      </channel>
    </rss>
    """
    alerts = parser.parse(xml_with_bad_item)
    assert len(alerts) == 2
    assert alerts[0].raw_payload.get("guid") == "RSS-001"
    assert alerts[1].raw_payload.get("guid") == "RSS-003"


def test_rss_parser_input_immutability():
    """Verify original XML tree element remains unmutated after parsing."""
    parser = RssParser()
    elem_tree = ET.parse(RSS_DATASET_PATH)
    root = elem_tree.getroot()

    xml_before = ET.tostring(root, encoding="utf-8")
    _ = parser.parse(elem_tree)
    xml_after = ET.tostring(root, encoding="utf-8")

    assert xml_before == xml_after
