# Stage 4 — RSS Parser Manual Verification Guide

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer  
**Stage:** Stage 4 — RSS Parser  
**Date:** 2026-08-03  

---

## 1. Executive Summary

This manual verification guide provides step-by-step CLI execution commands to test and verify the `RssParser` implementation. `RssParser` subclassing `BaseParser` extracts unnormalized alert fields from RSS XML format data into intermediate `ParsedAlert` objects without performing data normalization or schema transformations.

---

## 2. Prerequisites

Ensure the virtual environment is activated and dependencies are installed:

```bash
cd /Users/tkapilkishore/Desktop/alert-intelligence-engine
source .venv/bin/activate
```

---

## 3. Input Dataset

- **Input File:** `data/raw_alerts_rss.xml`
- **Format:** RSS XML version 2.0 format containing 10 disaster alert records (`<item>` XML nodes nested inside `<rss>/<channel>`).

---

## 4. Automated Verification Commands

Run the full automated test suite for Stage 4 using `pytest`:

```bash
./.venv/bin/pytest tests/test_rss_parser.py -v
```

**Expected Result:**
```
tests/test_rss_parser.py::test_rss_parser_imports_and_inheritance PASSED
tests/test_rss_parser.py::test_rss_parser_dataset_loading PASSED
tests/test_rss_parser.py::test_rss_parser_parsed_alert_baseline_contract PASSED
tests/test_rss_parser.py::test_rss_parser_field_extraction PASSED
tests/test_rss_parser.py::test_rss_parser_input_types PASSED
tests/test_rss_parser.py::test_rss_parser_malformed_input_resilience PASSED
tests/test_rss_parser.py::test_rss_parser_single_malformed_record_resilience PASSED
tests/test_rss_parser.py::test_rss_parser_input_immutability PASSED

============================== 8 passed in 0.06s ==============================
```

Run the entire project test suite to verify no regressions:

```bash
./.venv/bin/pytest tests/ -v
```

**Expected Result:** All 27 tests pass (8 RssParser tests + 7 CapParser tests + 6 JsonParser tests + 6 Foundation tests).

---

## 5. CLI Manual Verification Command

Execute the following Python one-liner to parse `data/raw_alerts_rss.xml` and inspect the output:

```bash
./.venv/bin/python3 -c "
from pathlib import Path
from src.parsers.rss_parser import RssParser

xml_path = Path('data/raw_alerts_rss.xml')
with open(xml_path, 'r', encoding='utf-8') as f:
    xml_content = f.read()

parser = RssParser()
alerts = parser.parse(xml_content)

print(f'Successfully parsed {len(alerts)} RSS XML alerts.\n')
print('Sample ParsedAlert Record [RSS-001]:')
print(f'  raw_hazard:     {alerts[0].raw_hazard}')
print(f'  raw_severity:   {alerts[0].raw_severity}')
print(f'  raw_location:   {alerts[0].raw_location}')
print(f'  raw_action:     {alerts[0].raw_action}')
print(f'  raw_start_time: {alerts[0].raw_start_time}')
print(f'  source:         {alerts[0].source}')
print(f'  source_format:  {alerts[0].source_format}')
print(f'  parse_warnings: {alerts[0].parse_warnings}')
print(f'  raw_payload:    {alerts[0].raw_payload}')
"
```

---

## 6. Sample Output Verification

```text
Successfully parsed 10 RSS XML alerts.

Sample ParsedAlert Record [RSS-001]:
  raw_hazard:     Urban Flood
  raw_severity:   RED ALERT
  raw_location:   Suryanagar Block 3
  raw_action:     Avoid low-lying roads and move valuables above ground level
  raw_start_time: Thu, 17 Jul 2025 12:00:00 +0530
  source:         Demo Disaster Alert Feed
  source_format:  rss
  parse_warnings: []
  raw_payload:    {'guid': 'RSS-001', 'title': 'RED ALERT: Urban Flood warning for Suryanagar Block 3', 'description': 'Urban Flood expected in Suryanagar Block 3. Action: Avoid low-lying roads and move valuables above ground level. Valid for next 48 hours.', 'pubDate': 'Thu, 17 Jul 2025 12:00:00 +0530'}
```

---

## 7. Verification Checklist

| Item | Requirement | Verification Method | Status |
|------|-------------|---------------------|--------|
| 1 | Class inheritance | `isinstance(RssParser(), BaseParser)` | PASS |
| 2 | Pure XML input handling | Accepts XML `str`, `bytes`, `ET.Element`, `ET.ElementTree`, `List[ET.Element]` without doing file I/O inside parser | PASS |
| 3 | Dataset alert count | Exactly 10 alerts extracted from `data/raw_alerts_rss.xml` | PASS |
| 4 | Flexible pattern extraction | Severity prefix, hazard, location, action extracted via lightweight regex without hardcoded assumptions | PASS |
| 5 | ParsedAlert baseline contract | `source_format == "rss"`, `parse_warnings` is a list, `raw_payload` is populated | PASS |
| 6 | Single record error isolation | Malformed `<item>` tag logs warning and skips item while continuing parsing | PASS |
| 7 | Input immutability | Input XML tree elements remain unmutated | PASS |
| 8 | Frozen scope compliance | No normalization, severity mapping, timestamp conversion, or Gemini calls | PASS |
