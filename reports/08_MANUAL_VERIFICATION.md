# Stage 8 — Manual Verification Guide

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer  
**Stage:** Stage 8 — Validation Engine  
**Date:** 2026-08-04  

---

# 1. Verification Overview

This document provides CLI instructions for manually verifying the **Stage 8 Validation Engine** using Python interactive REPL / script snippets.

---

# 2. Automated Test Execution

Run the complete test suite including all Stage 8 validation test cases:

```bash
.venv/bin/pytest -v
```

Expected output: `73 passed in 0.48s`.

---

# 3. Interactive CLI Manual Verification

You can verify `ValidationEngine` behavior directly via Python:

```bash
.venv/bin/python
```

Execute the following Python snippet in the shell:

```python
from src.validator import ValidationEngine
from src.schema import ParsedAlert, NormalizedAlert

engine = ValidationEngine()

# 1. Structural Validation Test
parsed = ParsedAlert(
    raw_hazard="Flood warning",
    source="IMD Feed",
    source_format="json",
    raw_payload={"id": "JSON-001"}
)
res_struct = engine.validate_structure(parsed)
print("Structural Valid:", res_struct.is_valid)
print("Structural Errors:", res_struct.errors)
print("Structural Warnings:", res_struct.warnings)

# 2. Schema Validation Test
normalized = NormalizedAlert(
    alert_id="JSON-001",
    source="IMD Feed",
    hazard_type="flood",
    severity="Moderate",
    urgency="Future",
    certainty="Likely",
    location_name="Nirmala",
    location_id="DIST-01",
    start_time="2025-07-17T03:00:00",
    end_time="2025-07-18T15:00:00",
    recommended_action="Avoid flooded roads",
    source_format="json",
    is_duplicate=False,
    parse_warnings=[]
)
res_schema = engine.validate_schema(normalized)
print("Schema Valid:", res_schema.is_valid)
print("Schema Errors:", res_schema.errors)
print("Schema Warnings:", res_schema.warnings)
```

### Expected Output

```
Structural Valid: True
Structural Errors: []
Structural Warnings: ['Missing raw severity', 'Missing raw location', 'Missing raw start_time', 'Missing raw end_time', 'Missing raw action']
Schema Valid: True
Schema Errors: []
Schema Warnings: []
```

---

# 4. Summary

Stage 8 has passed all automated and manual verification checks.
