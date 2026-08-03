# Stage 7 — Manual Verification Guide

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer  
**Stage:** Stage 7 — Normalization Engine  
**Date:** 2026-08-04  

---

# 1. Verification Overview

This document provides CLI instructions for manually verifying the **Stage 7 Normalization Engine** using Python interactive REPL / script snippets.

---

# 2. Automated Test Execution

Run the complete test suite including all Stage 7 mapper and normalization test modules:

```bash
.venv/bin/pytest -v
```

Expected output: `61 passed in 0.41s`.

---

# 3. Interactive CLI Manual Verification

You can verify `NormalizationEngine` behavior directly via Python:

```bash
.venv/bin/python
```

Execute the following Python snippet in the shell:

```python
from src.normalization import NormalizationEngine
from src.schema import ParsedAlert

# 1. Instantiate NormalizationEngine
engine = NormalizationEngine()

# 2. Construct a sample ParsedAlert
parsed = ParsedAlert(
    raw_hazard="Urban Flood",
    raw_severity="Orange",
    raw_urgency="Immediate",
    raw_certainty="Observed",
    raw_location="Devapur Block 2",
    raw_start_time="2025-07-17 03:00",
    raw_end_time="2025-07-18 15:00",
    raw_action="Avoid low-lying roads and move valuables above ground level.",
    source="Demo IMD Feed",
    source_format="json",
    raw_payload={"id": "JSON-001"}
)

# 3. Normalize
normalized = engine.normalize(parsed)

# 4. Inspect normalized output
print("Alert ID:", normalized.alert_id)
print("Hazard Type:", normalized.hazard_type)
print("Severity:", normalized.severity)
print("Urgency:", normalized.urgency)
print("Certainty:", normalized.certainty)
print("Location Name:", normalized.location_name)
print("Location ID:", normalized.location_id)
print("Start Time:", normalized.start_time)
print("End Time:", normalized.end_time)
print("Parse Warnings:", normalized.parse_warnings)
```

### Expected Output

```
Alert ID: JSON-001
Hazard Type: flood
Severity: Severe
Urgency: Immediate
Certainty: Observed
Location Name: Devapur Block 2
Location ID: BLK-03-2
Start Time: 2025-07-17T03:00:00
End Time: 2025-07-18T15:00:00
Parse Warnings: []
```

---

# 4. Summary

Stage 7 has passed all automated and manual verification checks.
