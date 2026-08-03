# Stage 1 — Manual Verification Guide

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer  
**Stage:** 1 — Project Foundation Infrastructure  
**Author:** Lead AI/ML Software Engineer  
**Date:** 2026-08-03  

---

# Executive Summary

**Can Stage 1 be manually verified?**

- **Infrastructure Verification:** **YES**. Stage 1 project structure, package imports, logger, abstract interface, and Pydantic models can be manually executed and verified via terminal commands and interactive Python shell.
- **End-to-End Dataset Processing Verification:** **NO**. Stage 1 intentionally contains zero parser logic, normalization logic, or pipeline execution logic. Processing raw datasets from `data/provided/` into `normalized_alerts.json` cannot occur in Stage 1.

---

# Part 1 — Stage 1 Infrastructure Manual Verification

The following manual verification steps confirm that Stage 1 foundation infrastructure operates correctly.

### Step 1: Environment Setup & Package Installation

Execute in terminal:

```bash
# Navigate to project root
cd /Users/tkapilkishore/Desktop/alert-intelligence-engine

# Verify virtual environment existence
python3 -m venv .venv

# Install Version 1.0 dependencies
.venv/bin/pip install -r requirements.txt
```

**Expected Output:**
```text
Successfully installed annotated-types feedparser lxml numpy packaging pandas pluggy pydantic pydantic-core pygments pytest python-dateutil python-dotenv rapidfuzz six typing-extensions typing-inspection
```

---

### Step 2: Automated Pytest Suite Execution

Execute in terminal:

```bash
.venv/bin/pytest tests/ -v
```

**Expected Output:**
```text
tests/test_foundation.py::test_package_imports PASSED                     [ 16%]
tests/test_foundation.py::test_base_parser_is_abstract PASSED              [ 33%]
tests/test_foundation.py::test_parsed_alert_instantiation PASSED           [ 50%]
tests/test_foundation.py::test_normalized_alert_instantiation PASSED       [ 66%]
tests/test_foundation.py::test_logger_initialization PASSED                [ 83%]
tests/test_foundation.py::test_utility_skeletons_exist PASSED              [100%]

============================== 6 passed in 0.23s ===============================
```

---

### Step 3: Interactive Python Shell Verification

Execute in terminal:

```bash
.venv/bin/python3 -c "
from src.constants import SUPPORTED_SOURCE_FORMATS, DEFAULT_LOG_NAME
from src.logger import get_logger
from src.schema import ParsedAlert, NormalizedAlert
from src.parsers.base_parser import BaseParser
from src.pipeline import Pipeline

logger = get_logger('manual_test')
logger.info('Logger initialized successfully!')

parsed = ParsedAlert(source='manual_test', source_format='json', raw_hazard='cyclone')
print(f'ParsedAlert instantiated: {parsed}')

normalized = NormalizedAlert(
    alert_id='ALT-100',
    source='manual_test',
    hazard_type='cyclone',
    severity='Severe',
    urgency='Immediate',
    certainty='Observed',
    location_name='Odisha Coast',
    recommended_action='Take shelter immediately',
    source_format='json'
)
print(f'NormalizedAlert instantiated: {normalized.alert_id} | {normalized.hazard_type}')
"
```

**Expected Output:**
```text
2026-08-03 12:30:00,000 - manual_test - INFO - Logger initialized successfully!
ParsedAlert instantiated: raw_hazard='cyclone' raw_severity=None raw_urgency=None raw_certainty=None raw_location=None raw_start_time=None raw_end_time=None raw_action=None source='manual_test' source_format='json' raw_payload={} parse_warnings=[]
NormalizedAlert instantiated: ALT-100 | cyclone
```

---

### Step 4: Abstract Base Class Constraint Check

Verify that `BaseParser` cannot be instantiated directly:

```bash
.venv/bin/python3 -c "
from src.parsers.base_parser import BaseParser
try:
    p = BaseParser()
except TypeError as e:
    print('PASS: BaseParser correctly prevented direct instantiation:', e)
"
```

**Expected Output:**
```text
PASS: BaseParser correctly prevented direct instantiation: Can't instantiate abstract class BaseParser without an implementation for abstract method 'parse'
```

---

# Verification Checklist (Stage 1)

- [x] Dependencies install cleanly without conflicts
- [x] Project modules import without `ModuleNotFoundError` or syntax errors
- [x] `BaseParser` raises `TypeError` when instantiated directly
- [x] `ParsedAlert` instantiates with required fields
- [x] `NormalizedAlert` instantiates and validates against domain enums
- [x] `get_logger` configures stdout logging stream correctly
- [x] All 6 foundation pytest cases pass (100% pass rate)

---

# Part 2 — Future Stages End-to-End Dataset Verification Plan

### Why End-to-End Dataset Verification is Not Applicable to Stage 1
Stage 1 is infrastructure only. Parsers (JSON, CAP, RSS, Plaintext) will be implemented incrementally in Stages 2 through 5. The Normalization Engine is built in Stage 7, Validation in Stage 8, Deduplication in Stage 9, and Pipeline Integration in Stage 10.

### Stage 10 & Stage 11 Dataset Verification Schedule
End-to-end dataset manual verification becomes meaningful at **Stage 10 (Pipeline Integration)** and **Stage 11 (Testing)**.

### What Kapil Will Manually Verify at Stage 10 & 11:
1. **Pipeline Batch Execution Command**:
   ```bash
   .venv/bin/python -m src.pipeline --input-dir data/provided/ --output outputs/normalized_alerts.json
   ```
2. **Output File Verification**:
   - Verify `outputs/normalized_alerts.json` exists.
   - Verify JSON output conforms exactly to `data/provided/expected_normalized_schema.json`.
3. **Dataset Ingestion Coverage**:
   - Verify JSON alerts from `raw_alerts_json.json` are parsed.
   - Verify CAP XML alerts from `raw_alerts_cap.xml` are parsed.
   - Verify RSS XML alerts from `raw_alerts_rss.xml` are parsed.
   - Verify Plaintext alerts from `raw_alerts_plaintext.txt` are parsed with Gemini fallback for incomplete fields.
4. **Reference Mapping Accuracy**:
   - Check mapped severities against `severity_mapping_reference.csv`.
   - Check mapped locations against `location_reference.csv`.
5. **Deduplication Verification**:
   - Confirm duplicate alerts have `is_duplicate = true` and unique alerts have `is_duplicate = false`.
6. **Golden Sample Instruction Compliance**:
   - Compare final `normalized_alerts.json` against rules defined in `golden_sample_instructions.json`.
