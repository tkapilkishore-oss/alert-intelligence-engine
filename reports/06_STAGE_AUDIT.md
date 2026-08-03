# Stage 6 — Gemini Fallback Engine Stage Audit

**Project Name:** Alert Intelligence Engine – Disaster Alert Parser & Normalizer  
**Stage:** Stage 6 — Gemini Fallback Engine  
**Auditor:** Lead AI/ML Software Engineer  
**Date:** 2026-08-04  

---

## 1. Executive Summary

This audit evaluates the Stage 6 implementation of `GeminiExtractor` in `src/gemini_extractor.py`, associated unit tests in `tests/test_gemini_extractor.py`, dependency updates in `requirements.txt`, and manual verification documentation.

The implementation strictly satisfies all Stage 6 objectives, incorporates all four user-mandated engineering improvements, adheres to frozen system architecture, enforces prompt versioning and input immutability, and passes 100% of the project regression test suite (46/46 tests).

---

## 2. Architecture Compliance Audit

| Architectural Principle | Compliance Status | Evidence / Implementation Details |
|-------------------------|-------------------|-----------------------------------|
| **Official GenAI SDK** | COMPLIANT | Uses official `google-genai` SDK (`from google import genai`) instead of manual REST requests. Added `google-genai` to `requirements.txt`. |
| **Input Immutability** | COMPLIANT | `enrich(alert)` creates a deep copy (`alert.model_copy(deep=True)`), merges extracted values into the copy, and leaves the incoming `ParsedAlert` completely untouched. |
| **Prompt Versioning** | COMPLIANT | Module defines `PROMPT_VERSION = "v1"` and incorporates the version identifier inside `_build_prompt()`. |
| **Strict JSON Key Validation** | COMPLIANT | Returned JSON is validated against `ALLOWED_GEMINI_KEYS`. If unauthorized extra keys are present, the response is discarded, a `parse_warning` is appended, and partial inference is avoided. |
| **Trigger Evaluation** | COMPLIANT | Gemini is invoked ONLY if `raw_hazard`, `raw_severity`, or `raw_location` is missing. Complete alerts return immediately without calling Gemini API. |
| **Merge Policy (Parser Wins)** | COMPLIANT | Existing parser values in `ParsedAlert` are never overwritten by Gemini response data. Gemini only populates `None` or empty fields. |
| **Source Payload Isolation** | COMPLIANT | Extractor reads original alert text strictly from `alert.raw_payload["original_text"]`. Never reconstructs text from parsed fields. |
| **Fault Resilience** | COMPLIANT | Gracefully catches API errors, JSON parse failures, missing API keys, timeouts, empty responses, and malformed objects. Appends explicit `parse_warnings` and continues safely. |
| **Secret Management** | COMPLIANT | Reads `GEMINI_API_KEY` strictly from `.env` using `python-dotenv`. Never prints or logs API keys. |
| **Isolated Unit Testing** | COMPLIANT | Unit tests in `tests/test_gemini_extractor.py` strictly use `unittest.mock` to prevent real network calls during pytest execution. |

---

## 3. Mandatory Engineering Improvement Audit

| Improvement # | Requirement | Implementation Status | Evidence / Location |
|---------------|-------------|-----------------------|---------------------|
| **1** | Replace manual `urllib` calls with official `google-genai` SDK | VERIFIED | `src/gemini_extractor.py` uses `from google import genai`. `requirements.txt` updated. |
| **2** | Deep copy incoming `ParsedAlert` to guarantee input immutability | VERIFIED | `src/gemini_extractor.py#L48`: `enriched_alert = alert.model_copy(deep=True)`. Tested in `test_gemini_input_immutability`. |
| **3** | Prompt versioning with `PROMPT_VERSION = "v1"` | VERIFIED | `src/gemini_extractor.py#L16`: `PROMPT_VERSION: str = "v1"`. Included in `_build_prompt()`. Tested in `test_prompt_version_constant`. |
| **4** | Reject JSON responses containing unauthorized keys | VERIFIED | `src/gemini_extractor.py#L107`: `extra_keys = set(extracted_data.keys()) - ALLOWED_GEMINI_KEYS`. Tested in `test_gemini_unexpected_json_keys_rejection`. |

---

## 4. Code Quality & Ponytail Compliance Audit

- **Minimal & Focused Code:** ~170 LOC in `src/gemini_extractor.py`. Focused implementation without redundant wrapper classes.
- **Single Responsibility:** `GeminiExtractor` is strictly responsible for fallback field enrichment. Performs zero file I/O, parsing, or normalization.
- **Explicit Typing:** Complete type annotations on methods, arguments, return values, and constants.
- **No Unrequested Dependencies:** Added only the single authorized dependency `google-genai`.
- **Zero Magic Numbers:** Default model identifier (`gemini-2.5-flash`), allowed key set (`ALLOWED_GEMINI_KEYS`), and prompt version (`PROMPT_VERSION`) declared as explicit constants.

---

## 5. Dependency Graph

```
requirements.txt
    └── google-genai

src/gemini_extractor.py
    ├── google.genai (genai.Client, types)
    ├── dotenv (load_dotenv)
    ├── src.schema (ParsedAlert)
    ├── src.logger (get_logger)
    └── json / os (Standard Library)
```

---

## 6. Technical Debt Assessment

- **Identified Technical Debt:** None.
- **Edge Cases Handled:**
  - Complete alerts with all required fields present (Gemini skipped).
  - Incoming `ParsedAlert` immutability (deep copy returned).
  - Responses with markdown code fences (` ```json `).
  - Non-object JSON responses or invalid JSON strings.
  - Unexpected extra JSON keys (rejected with warning).
  - Missing `GEMINI_API_KEY` in environment.
  - Missing `original_text` in `raw_payload`.
  - Network timeouts, HTTP errors, rate limit exceeded, and API exceptions.

---

## 7. Risk Analysis

| Risk | Level | Mitigation |
|------|-------|------------|
| API outage / network error | LOW | Wrapped in try/except boundary; logs warning, appends `parse_warning`, and returns original alert safely. |
| Hallucinated extra JSON keys | LOW | Validated against `ALLOWED_GEMINI_KEYS`; extra keys trigger rejection and `parse_warning`. |
| Overwriting parser output | NONE | Enforced merge policy where existing parser fields are never overwritten (`parser wins`). |
| Mutating input objects | NONE | Enforced deep copy via `.model_copy(deep=True)`; verified in automated tests. |

---

## 8. Recommendation

**APPROVED FOR STAGE 6 FREEZE.**

The `GeminiExtractor` implementation satisfies all architectural, engineering, quality, testing, and safety requirements. Proceeding to Stage 7 (Normalization Engine) is recommended upon authorization.
