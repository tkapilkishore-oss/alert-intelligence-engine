# Stage 2 — Manual Verification Guide

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer

**Stage 2:** JSON Parser

**Date:** 2026-08-03

---

## 1. Overview

This document provides step-by-step manual verification instructions for validating the `JsonParser` implementation developed in Stage 2. 

The verification uses CLI execution without any external UI, web server, or framework dependencies.

---

## 2. Exact Input File

- **File Path:** `data/raw_alerts_json.json`
- **File Format:** JSON Array containing 14 raw disaster alert objects.
- **Field Aliases Present:**
  - Hazard: `hazard`, `event`, `warningType`
  - Location: `location`, `area`, `district`
  - Severity: `severity`, `level`, `severity_text`
  - Start Time: `valid_from`, `onset`, `startTime`
  - End Time: `valid_to`, `endTime`, `expires`
  - Action: `recommended_action`, `advice`, `instruction`

---

## 3. Local Verification Command

Execute the following terminal command from the project root directory using the project virtual environment:

```bash
.venv/bin/python3 -c "
import json
from pathlib import Path
from src.parsers.json_parser import JsonParser

dataset_path = Path('data/raw_alerts_json.json')
with open(dataset_path, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

parser = JsonParser()
alerts = parser.parse(raw_data)

print(f'=== MANUALLY VERIFIED JSON PARSER ===')
print(f'Input File: {dataset_path}')
print(f'Parsed Records Count: {len(alerts)}')

sample = alerts[0]
print(f'\nSample Record [0] ParsedAlert:')
print(f'  raw_hazard:    {sample.raw_hazard}')
print(f'  raw_severity:  {sample.raw_severity}')
print(f'  raw_location:  {sample.raw_location}')
print(f'  raw_start_time:{sample.raw_start_time}')
print(f'  raw_end_time:  {sample.raw_end_time}')
print(f'  raw_action:    {sample.raw_action}')
print(f'  source:        {sample.source}')
print(f'  source_format: {sample.source_format}')

assert len(alerts) == 14, f'Expected 14 records, got {len(alerts)}'
print('\n[SUCCESS] Manual verification passed!')
"
```

---

## 4. Expected ParsedAlert Output Structure

Each record returned by `JsonParser.parse()` must be an instance of `ParsedAlert` with the following attributes:

```python
ParsedAlert(
    raw_hazard="Urban Flood",
    raw_severity="Moderate",
    raw_urgency="Future",
    raw_certainty="Likely",
    raw_location="Nirmala",
    raw_start_time="2025-07-17 03:00",
    raw_end_time="2025-07-18 15:00",
    raw_action="Avoid low-lying roads and move valuables above ground level.",
    source="Demo IMD Feed",
    source_format="json",
    raw_payload={ ... },
    parse_warnings=[]
)
```

---

## 5. Expected Record Counts

| Input Target | Total Raw Records | Parsed Records Returned | Skipped / Warning |
|--------------|------------------|-------------------------|-------------------|
| `data/raw_alerts_json.json` | 14 | 14 | 0 |
| Single Alert Dict | 1 | 1 | 0 |
| JSON String | N | N | 0 |
| Malformed List `[dict, "bad", 123]` | 3 | 1 | 2 (logged warnings) |

---

## 6. Automated Verification Commands

Run the full pytest suite:

```bash
.venv/bin/pytest tests/test_json_parser.py -v
```

Expected Output:
```text
tests/test_json_parser.py::test_json_parser_imports_and_inheritance PASSED
tests/test_json_parser.py::test_json_parser_dataset_loading PASSED
tests/test_json_parser.py::test_json_parser_field_alias_resolution PASSED
tests/test_json_parser.py::test_json_parser_input_types PASSED
tests/test_json_parser.py::test_json_parser_malformed_input_resilience PASSED
tests/test_json_parser.py::test_json_parser_input_immutability PASSED
```

---

## 7. Verification Checklist

- [x] CLI execution command provided and tested.
- [x] Input file `data/raw_alerts_json.json` verified.
- [x] Record count exact match (14 records).
- [x] Raw values preserved without normalization or transformation.
- [x] Field aliases resolved correctly (`event`, `hazard`, `warningType`, etc.).
- [x] Record-level exception handling verified with malformed elements.
- [x] Read-only immutability verified (input data not mutated).
- [x] Zero UI/web frameworks created (CLI only).
