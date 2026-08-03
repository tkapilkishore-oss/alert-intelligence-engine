# Stage 5 — Plaintext Parser Manual Verification Guide

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer  
**Stage:** Stage 5 — Plaintext Parser  
**Date:** 2026-08-04  

---

## 1. Executive Summary

This manual verification guide provides step-by-step CLI execution commands to test and verify the `PlaintextParser` implementation. `PlaintextParser` subclassing `BaseParser` extracts unnormalized alert fields from unstructured plaintext alert notifications into intermediate `ParsedAlert` objects without performing data normalization or schema transformations.

---

## 2. Prerequisites

Ensure the virtual environment is activated and dependencies are installed:

```bash
cd /Users/tkapilkishore/Desktop/alert-intelligence-engine
source .venv/bin/activate
```

---

## 3. Input Dataset

- **Input File:** `data/raw_alerts_plaintext.txt`
- **Format:** Unstructured plain text containing 9 disaster alert notifications in varied layouts (pipe-delimited, colon-formatted, dash-formatted, malformed natural language).

---

## 4. Automated Verification Commands

Run the full automated test suite for Stage 5 using `pytest`:

```bash
./.venv/bin/pytest tests/test_plaintext_parser.py -v
```

**Expected Result:**
```
tests/test_plaintext_parser.py::test_plaintext_parser_imports_and_inheritance PASSED
tests/test_plaintext_parser.py::test_plaintext_parser_dataset_loading PASSED
tests/test_plaintext_parser.py::test_plaintext_parser_parsed_alert_baseline_contract PASSED
tests/test_plaintext_parser.py::test_plaintext_parser_field_extraction PASSED
tests/test_plaintext_parser.py::test_plaintext_parser_malformed_and_missing_fields PASSED
tests/test_plaintext_parser.py::test_plaintext_parser_input_types PASSED
tests/test_plaintext_parser.py::test_plaintext_parser_malformed_input_resilience PASSED
tests/test_plaintext_parser.py::test_plaintext_parser_input_immutability PASSED

============================== 8 passed in 0.05s ==============================
```

Run the entire project test suite to verify no regressions:

```bash
./.venv/bin/pytest tests/ -v
```

**Expected Result:** All 35 tests pass (8 PlaintextParser tests + 8 RssParser tests + 7 CapParser tests + 6 JsonParser tests + 6 Foundation tests).

---

## 5. CLI Manual Verification Command

Execute the following Python one-liner to parse `data/raw_alerts_plaintext.txt` and inspect the output:

```bash
./.venv/bin/python3 -c "
from pathlib import Path
from src.parsers.plaintext_parser import PlaintextParser

txt_path = Path('data/raw_alerts_plaintext.txt')
txt_content = txt_path.read_text(encoding='utf-8')

parser = PlaintextParser()
alerts = parser.parse(txt_content)

print(f'Successfully parsed {len(alerts)} Plaintext alerts.\n')
print('Sample ParsedAlert Record [PT-001]:')
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
Successfully parsed 9 Plaintext alerts.

Sample ParsedAlert Record [PT-001]:
  raw_hazard:     flood warning
  raw_severity:   Severe
  raw_location:   Devapur
  raw_action:     avoid river-side roads
  raw_start_time: starts 2025-07-16 08:00
  source:         ALERT PT-001
  source_format:  plaintext
  parse_warnings: []
  raw_payload:    {'original_text': 'ALERT PT-001 | Devapur | Severe flood warning | starts 2025-07-16 08:00 | avoid river-side roads', 'detected_pattern': 'pipe'}
```

---

## 7. Verification Checklist

| Item | Requirement | Verification Method | Status |
|------|-------------|---------------------|--------|
| 1 | Class inheritance | `isinstance(PlaintextParser(), BaseParser)` | PASS |
| 2 | Pure input handling | Accepts `str`, `bytes`, `List[str]` without doing file I/O inside parser | PASS |
| 3 | Dataset alert count | Exactly 9 alerts extracted from `data/raw_alerts_plaintext.txt` | PASS |
| 4 | Preserve original line | `raw_payload["original_text"]` populated with untouched original string | PASS |
| 5 | Pattern helper dispatch | Modular pattern detection and pattern helper methods | PASS |
| 6 | Explicit parse warnings | Warnings like `missing severity`, `missing location`, `missing start_time` appended | PASS |
| 7 | Single record error isolation | Malformed text lines log warning and skip line without crashing batch | PASS |
| 8 | Input immutability | Input data structures remain unmutated | PASS |
| 9 | Frozen scope compliance | No normalization, severity mapping, timestamp conversion, or Gemini calls | PASS |
