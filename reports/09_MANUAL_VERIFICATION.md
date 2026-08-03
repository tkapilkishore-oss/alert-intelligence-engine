# Stage 9 — Manual Verification Guide

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer  
**Stage:** Stage 9 — Deduplication Engine  
**Date:** 2026-08-04  

---

# 1. Verification Overview

This document provides CLI instructions for manually verifying the **Stage 9 Deduplication Engine** using Python interactive REPL / script snippets.

---

# 2. Automated Test Execution

Run the complete test suite including all Stage 9 deduplication test cases:

```bash
.venv/bin/pytest -v
```

Expected output: `85 passed in 0.52s`.

---

# 3. Interactive CLI Manual Verification

You can verify `DeduplicationEngine` behavior directly via Python:

```bash
.venv/bin/python
```

Execute the following Python snippet in the shell:

```python
from src.deduplicator import DeduplicationEngine
from src.schema import NormalizedAlert

engine = DeduplicationEngine()

# 1. Create original canonical alert
alert1 = NormalizedAlert(
    alert_id="JSON-001",
    source="Demo IMD Feed",
    hazard_type="flood",
    severity="Moderate",
    urgency="Future",
    certainty="Likely",
    location_name="Nirmala",
    location_id="DIST-001",
    start_time="2025-07-17T03:00:00",
    end_time="2025-07-18T15:00:00",
    recommended_action="Avoid low-lying roads and move valuables above ground level.",
    source_format="json",
    is_duplicate=False,
    parse_warnings=[]
)

# 2. Create duplicate alert from another source with same event details
alert2 = NormalizedAlert(
    alert_id="CAP-005",
    source="District Control Room",
    hazard_type="flood",
    severity="Moderate",
    urgency="Future",
    certainty="Likely",
    location_name="Nirmala",
    location_id="DIST-001",
    start_time="2025-07-17T03:00:00",
    end_time="2025-07-18T15:00:00",
    recommended_action="Avoid low-lying roads and move valuables above ground level.",
    source_format="cap_xml",
    is_duplicate=False,
    parse_warnings=[]
)

# 3. Create distinct alert with different location and hazard
alert3 = NormalizedAlert(
    alert_id="JSON-002",
    source="State EOC Demo",
    hazard_type="earthquake",
    severity="Extreme",
    urgency="Immediate",
    certainty="Observed",
    location_name="Kalyanpur",
    location_id="DIST-002",
    start_time="2025-07-15T14:00:00",
    end_time="2025-07-17T14:00:00",
    recommended_action="Take cover under sturdy furniture.",
    source_format="json",
    is_duplicate=False,
    parse_warnings=[]
)

results = engine.deduplicate([alert1, alert2, alert3])

print("Total items:", len(results))
print("Alert 1 is_duplicate:", results[0].is_duplicate)
print("Alert 2 is_duplicate:", results[1].is_duplicate)
print("Alert 3 is_duplicate:", results[2].is_duplicate)
```

### Expected Output

```
Total items: 3
Alert 1 is_duplicate: False
Alert 2 is_duplicate: True
Alert 3 is_duplicate: False
```

---

# 4. Summary

Stage 9 has passed all automated and manual verification checks.
