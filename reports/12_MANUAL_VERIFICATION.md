# Stage 12 — Manual Verification Guide

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer  
**Stage:** Stage 12 — Natural Language Entry Layer & Project Finalization  
**Date:** 2026-08-05  

---

# 1. Verification Overview

This document provides CLI instructions for manually verifying **Stage 12 — Natural Language Entry Layer & Project Finalization** using the showcase demonstration script `demo.py` and Python interactive REPL snippets.

---

# 2. Automated Test Execution

Run the complete test suite including all Stage 12 Natural Language Entry Layer test cases and all regression tests:

```bash
# Run Stage 12 unit test suite
.venv/bin/pytest tests/test_nlp_processor.py -v

# Run full project test suite across all 12 stages
.venv/bin/pytest -v
```

Expected output: `123 passed in 2.03s`.

---

# 3. CLI Showcase Verification

Run the project CLI showcase demonstration:

```bash
.venv/bin/python demo.py
```

### Expected Output Summary

```
================================================================================
 ALERT INTELLIGENCE ENGINE — STAGE 12 SYSTEM DEMONSTRATION
================================================================================

--- 1. JSON Alert Processing ---
Parsed Count: 14
Duplicate Count: 1
Sample Normalized Alert (First Record):
{
  "alert_id": "JSON-001",
  "source": "IMD_HYDERABAD",
  "hazard_type": "flood",
  "severity": "Severe",
  ...
}

--- 2. CAP XML Alert Processing ---
Parsed Count: 8
Duplicate Count: 0

--- 3. RSS XML Alert Processing ---
Parsed Count: 10
Duplicate Count: 0

--- 4. Plaintext Alert Processing ---
Parsed Count: 9
Duplicate Count: 1

--- 5. Natural Language Layer Processing ---
Input Prompt: "Heavy rainfall is expected tomorrow morning in Devapur. People should avoid flooded roads."
Parsed Count: 1
Duplicate Count: 0
Normalized Output Alert:
{
  "alert_id": "PLAINTEXT-UNKNOWN",
  "source": "Natural Language Entry Layer",
  ...
}

================================================================================
 SEQUENTIAL PROCESSING SUMMARY ACROSS ALL FORMATS
================================================================================
JSON : 14
CAP : 8
RSS : 10
PLAINTEXT : 9

TOTAL ALERTS : 41
TOTAL DUPLICATES : 2
================================================================================
```

---

# 4. Interactive REPL Verification

Verify `NaturalLanguageProcessor` and `AlertPipeline.process_natural_language` directly via Python REPL:

```bash
.venv/bin/python
```

Run the following Python snippet:

```python
from src.nlp_processor import NaturalLanguageProcessor
from src.pipeline import AlertPipeline

# 1. Test NaturalLanguageProcessor isolation
processor = NaturalLanguageProcessor()
parsed = processor.process("Lightning reported near Vanasthal.")
print("Source:", parsed.source)
print("Payload:", parsed.raw_payload)

# 2. Test AlertPipeline natural language entry point
pipeline = AlertPipeline()
normalized_list = pipeline.process_natural_language("Heavy rainfall in Devapur.")
print("Normalized Count:", len(normalized_list))
print("Normalized Source:", normalized_list[0].source)
```

---

# 5. Summary

Stage 12 has passed all automated and manual verification checks. The project is fully functional, documented, tested, and ready for submission.
