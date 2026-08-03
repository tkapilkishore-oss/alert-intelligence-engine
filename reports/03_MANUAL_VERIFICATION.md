# Stage 3 — CAP XML Parser Manual Verification Guide

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer  
**Stage:** Stage 3 — CAP XML Parser  
**Date:** 2026-08-03  

---

## 1. Executive Summary

This manual verification guide provides step-by-step CLI execution commands to test and verify the `CapParser` implementation. `CapParser` subclassing `BaseParser` extracts unnormalized alert fields from Common Alerting Protocol (CAP) XML format data into intermediate `ParsedAlert` objects without performing data normalization or schema transformations.

---

## 2. Prerequisites

Ensure the virtual environment is activated and dependencies are installed:

```bash
cd /Users/tkapilkishore/Desktop/alert-intelligence-engine
source .venv/bin/activate
```

---

## 3. Input Dataset

- **Input File:** `data/raw_alerts_cap.xml`
- **Format:** CAP XML format containing 8 disaster alert records (`<alert>` XML nodes nested inside `<alerts>`).

---

## 4. Automated Verification Commands

Run the full automated test suite using `pytest`:

```bash
./.venv/bin/pytest tests/test_cap_parser.py -v
```

**Expected Result:**
```
tests/test_cap_parser.py::test_cap_parser_imports_and_inheritance PASSED
tests/test_cap_parser.py::test_cap_parser_dataset_loading PASSED
tests/test_cap_parser.py::test_cap_parser_field_extraction PASSED
tests/test_cap_parser.py::test_cap_parser_input_types PASSED
tests/test_cap_parser.py::test_cap_parser_malformed_input_resilience PASSED
tests/test_cap_parser.py::test_cap_parser_single_malformed_record_resilience PASSED
tests/test_cap_parser.py::test_cap_parser_input_immutability PASSED

============================== 7 passed in 0.05s ==============================
```

Run the entire project test suite to verify no regressions:

```bash
./.venv/bin/pytest tests/ -v
```

**Expected Result:** All 19 tests pass (7 CapParser tests + 6 JsonParser tests + 6 Foundation tests).

---

## 5. CLI Manual Verification Command

Execute the following Python one-liner to parse `data/raw_alerts_cap.xml` and inspect the output:

```bash
./.venv/bin/python3 -c "
from pathlib import Path
from src.parsers.cap_parser import CapParser

xml_path = Path('data/raw_alerts_cap.xml')
with open(xml_path, 'r', encoding='utf-8') as f:
    xml_content = f.read()

parser = CapParser()
alerts = parser.parse(xml_content)

print(f'Successfully parsed {len(alerts)} CAP XML alerts.\n')
print('Sample ParsedAlert Record [CAP-001]:')
print(f'  raw_hazard:     {alerts[0].raw_hazard}')
print(f'  raw_severity:   {alerts[0].raw_severity}')
print(f'  raw_urgency:    {alerts[0].raw_urgency}')
print(f'  raw_certainty:  {alerts[0].raw_certainty}')
print(f'  raw_location:   {alerts[0].raw_location}')
print(f'  raw_start_time: {alerts[0].raw_start_time}')
print(f'  raw_end_time:   {alerts[0].raw_end_time}')
print(f'  raw_action:     {alerts[0].raw_action}')
print(f'  source:         {alerts[0].source}')
print(f'  source_format:  {alerts[0].source_format}')
"
```

---

## 6. Sample Output Verification

```text
Successfully parsed 8 CAP XML alerts.

Sample ParsedAlert Record [CAP-001]:
  raw_hazard:     Lightning
  raw_severity:   Severe
  raw_urgency:    Expected
  raw_certainty:  Observed
  raw_location:   Vanasthal
  raw_start_time: 2025-07-18T21:00:00+05:30
  raw_end_time:   2025-07-19T13:00:00+05:30
  raw_action:     Stay indoors and avoid open fields or isolated trees.
  source:         weather-demo@example.org
  source_format:  cap_xml
```

---

## 7. Verification Checklist

| Item | Requirement | Verification Method | Status |
|------|-------------|---------------------|--------|
| 1 | Class inheritance | `isinstance(CapParser(), BaseParser)` | PASS |
| 2 | Pure XML input handling | Accepts XML `str`, `bytes`, `ET.Element`, `ET.ElementTree` without doing file I/O inside parser | PASS |
| 3 | Dataset alert count | Exactly 8 alerts extracted from `data/raw_alerts_cap.xml` | PASS |
| 4 | Field extraction | All nested fields (`<event>`, `<severity>`, `<urgency>`, `<certainty>`, `<onset>`, `<expires>`, `<areaDesc>`, `<instruction>`) extracted cleanly | PASS |
| 5 | Source format tag | `source_format == "cap_xml"` on all returned `ParsedAlert` objects | PASS |
| 6 | Single record error isolation | Malformed `<alert>` element logs warning and skips item while continuing parsing | PASS |
| 7 | Input immutability | Input XML tree elements remain unmutated | PASS |
| 8 | Frozen scope compliance | No normalization, severity mapping, timestamp conversion, or Gemini calls | PASS |
