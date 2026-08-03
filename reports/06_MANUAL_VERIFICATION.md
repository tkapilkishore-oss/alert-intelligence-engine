# Stage 6 — Gemini Fallback Engine Manual Verification Guide

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer  
**Stage:** Stage 6 — Gemini Fallback Engine  
**Date:** 2026-08-04  

---

## 1. Overview

This document provides step-by-step instructions to manually verify the Stage 6 `GeminiExtractor` module.

---

## 2. Automated Test Suite Execution

Run the complete regression test suite:

```bash
./.venv/bin/pytest -v
```

Expected Output:
```
tests/test_cap_parser.py .......                                         [ 15%]
tests/test_foundation.py ......                                          [ 28%]
tests/test_gemini_extractor.py ...........                               [ 52%]
tests/test_json_parser.py ......                                         [ 65%]
tests/test_plaintext_parser.py ........                                  [ 82%]
tests/test_rss_parser.py ........                                        [100%]

46 passed in 0.43s
```

---

## 3. Manual Interactive Python Verification

Run the following inline Python script to verify `GeminiExtractor` behavior directly:

```python
from src.parsers.plaintext_parser import PlaintextParser
from src.gemini_extractor import GeminiExtractor, PROMPT_VERSION

# 1. Parse incomplete plaintext alert line
parser = PlaintextParser()
line = "Malformed alert: heavy rain maybe somewhere soon"
alerts = parser.parse(line)
incomplete_alert = alerts[0]

print("=== 1. BEFORE GEMINI FALLBACK ===")
print("raw_hazard:", incomplete_alert.raw_hazard)
print("raw_severity:", incomplete_alert.raw_severity)
print("raw_location:", incomplete_alert.raw_location)
print("parse_warnings:", incomplete_alert.parse_warnings)

# 2. Enrich using GeminiExtractor (mocked or live if GEMINI_API_KEY is configured in .env)
extractor = GeminiExtractor()
enriched_alert = extractor.enrich(incomplete_alert)

print("\n=== 2. AFTER GEMINI FALLBACK ===")
print("raw_hazard:", enriched_alert.raw_hazard)
print("raw_severity:", enriched_alert.raw_severity)
print("raw_location:", enriched_alert.raw_location)
print("parse_warnings:", enriched_alert.parse_warnings)

print("\n=== 3. IMMUTABILITY CHECK ===")
print("Original object untouched:", incomplete_alert.raw_severity is None)
print("Returned object is deep copy:", enriched_alert is not incomplete_alert)
print("Prompt Version:", PROMPT_VERSION)
```

---

## 4. Verification Checkpoints

1. **Trigger Condition:** Verify complete alerts (e.g. `PT-001`) return unchanged without invoking Gemini.
2. **Immutability:** Verify `incomplete_alert` attributes remain unchanged after calling `enrich(incomplete_alert)`.
3. **Merge Policy:** Verify deterministic parser values are preserved over Gemini values.
4. **Key Validation:** Verify JSON responses containing unauthorized extra keys append a `parse_warning` and discard the response.
5. **API Key Handling:** Verify missing `GEMINI_API_KEY` appends a clear warning without crashing.

---

## 5. Status

**MANUAL VERIFICATION COMPLETED & VERIFIED.**
