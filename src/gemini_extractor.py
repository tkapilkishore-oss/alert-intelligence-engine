"""Gemini Fallback Engine module for Alert Intelligence Engine."""

import json
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types
# pyrefly: ignore [missing-import]
from google.genai.errors import APIError

from src.logger import get_logger
from src.schema import ParsedAlert

logger = get_logger(__name__)

PROMPT_VERSION: str = "v2"
DEFAULT_GEMINI_MODEL: str = "gemini-3.6-flash"
CANDIDATE_GEMINI_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest"]

ALLOWED_GEMINI_KEYS: Set[str] = {
    "raw_hazard",
    "raw_severity",
    "raw_urgency",
    "raw_certainty",
    "raw_location",
    "raw_start_time",
    "raw_end_time",
    "raw_action",
}


class GeminiExtractor:
    """Fallback enrichment module using Google Gemini API to extract missing alert fields."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        """Initialize GeminiExtractor with optional API key and model name.

        Args:
            api_key: Optional API key override. Reads from .env GEMINI_API_KEY by default.
            model_name: Optional Gemini model identifier to query. Reads from GEMINI_MODEL if absent.
        """
        load_dotenv()
        env_key = os.getenv("GEMINI_API_KEY")
        if not env_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                    env_key = str(st.secrets.get("GEMINI_API_KEY") or "").strip()
            except Exception:
                pass
        self._api_key = api_key if api_key is not None else env_key
        env_model = os.getenv("GEMINI_MODEL")
        if model_name:
            self._model_name = model_name
        elif env_model:
            self._model_name = env_model
        else:
            self._model_name = DEFAULT_GEMINI_MODEL

    def enrich(self, alert: ParsedAlert) -> ParsedAlert:
        """Enrich an incomplete ParsedAlert using Gemini fallback.

        Args:
            alert: Unmodified incoming ParsedAlert object.

        Returns:
            ParsedAlert: A deep copy of ParsedAlert, enriched if required, original untouched.
        """
        # Rule: Never mutate incoming alert; create a deep copy first.
        enriched_alert = alert.model_copy(deep=True)

        # Trigger check: Invoke Gemini ONLY if required fields are missing.
        if not self._is_enrichment_required(enriched_alert):
            logger.debug("Gemini fallback skipped: alert already has raw_hazard, raw_severity, and raw_location.")
            return enriched_alert

        if not self._api_key:
            enriched_alert.parse_warnings.append(
                "Gemini fallback skipped: GEMINI_API_KEY missing in environment"
            )
            logger.warning("Gemini fallback skipped due to missing API key.")
            return enriched_alert

        original_text = enriched_alert.raw_payload.get("original_text")
        if not original_text:
            enriched_alert.parse_warnings.append(
                "Gemini fallback skipped: missing original_text in raw_payload"
            )
            logger.warning("Gemini fallback skipped due to missing original_text.")
            return enriched_alert

        prompt = self._build_prompt(original_text)
        start_time = time.perf_counter()

        response_text, model_used, retry_count, fallback_used, error_msg = self._call_gemini_with_resilience(prompt)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        if error_msg or not response_text:
            msg = error_msg or "Gemini fallback failed: empty response from API"
            enriched_alert.parse_warnings.append(msg)
            logger.warning(msg)
            logger.debug(
                f"Gemini call failed. Duration: {duration_ms:.1f}ms, Retries: {retry_count}, Fallback Used: {fallback_used}"
            )
            return enriched_alert

        logger.debug("Raw Gemini response:\n%s", response_text)
        cleaned_text = self._sanitize_json_response(response_text)

        try:
            extracted_data = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.warning(
                f"Gemini JSON decoding failed.\n"
                f"Original Response: {response_text}\n"
                f"Sanitized Response: {cleaned_text}\n"
                f"JSONDecodeError: {e}"
            )
            msg = f"Gemini fallback failed: invalid JSON response ({e})"
            enriched_alert.parse_warnings.append(msg)
            return enriched_alert

        if not isinstance(extracted_data, dict):
            msg = "Gemini fallback failed: response JSON is not an object"
            enriched_alert.parse_warnings.append(msg)
            logger.warning(msg)
            return enriched_alert

        # Validate that returned JSON contains ONLY allowed keys.
        extra_keys = set(extracted_data.keys()) - ALLOWED_GEMINI_KEYS
        if extra_keys:
            msg = (
                f"Gemini fallback rejected: unexpected keys in JSON response "
                f"({', '.join(sorted(extra_keys))})"
            )
            enriched_alert.parse_warnings.append(msg)
            logger.warning(msg)
            return enriched_alert

        # Filter and sanitize values prior to merge
        sanitized_data = {k: v for k, v in extracted_data.items() if k in ALLOWED_GEMINI_KEYS and v is not None}

        # Merge policy: Parser always wins, Gemini only fills missing fields.
        populated_fields = self._merge_extracted_fields(enriched_alert, sanitized_data)

        logger.debug(
            f"Gemini enrichment succeeded. Model: {model_used}, Prompt Version: {PROMPT_VERSION}, "
            f"Duration: {duration_ms:.1f}ms, Retries: {retry_count}, Fallback Used: {fallback_used}, "
            f"Populated Fields: {populated_fields}"
        )

        return enriched_alert

    def _call_gemini_with_resilience(
        self, prompt: str
    ) -> Tuple[Optional[str], str, int, bool, Optional[str]]:
        """Execute Gemini call with exponential backoff and candidate model fallback chain.

        Returns:
            Tuple[Optional[str], str, int, bool, Optional[str]]:
                (response_text, model_used, retry_count, fallback_used, error_message)
        """
        candidate_models = [self._model_name]
        for m in CANDIDATE_GEMINI_MODELS:
            if m not in candidate_models:
                candidate_models.append(m)

        client = genai.Client(api_key=self._api_key)
        total_retries = 0
        primary_model = candidate_models[0]

        last_error: Optional[str] = None

        try:
            import importlib.metadata
            sdk_version = importlib.metadata.version("google-genai")
        except Exception:
            sdk_version = "UNKNOWN"

        key_prefix = (self._api_key[:5] + "...") if self._api_key else "None"

        for model_idx, model_candidate in enumerate(candidate_models):
            fallback_used = (model_candidate != primary_model)

            for attempt in range(2):  # Try primary attempt + 1 retry on 429
                if attempt > 0:
                    total_retries += 1
                    time.sleep(1.0)  # Short exponential backoff delay before retry

                try:
                    logger.debug(
                        f"[GEMINI REQUEST DIAGNOSTIC] Model: '{model_candidate}', "
                        f"Key Prefix: '{key_prefix}', Client Type: '{type(client).__name__}', "
                        f"SDK Version: '{sdk_version}', Prompt Length: {len(prompt)}"
                    )
                    response = client.models.generate_content(
                        model=model_candidate,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                        ),
                    )
                    if response and response.text:
                        logger.info(f"Gemini extraction succeeded using model '{model_candidate}'.")
                        return response.text, model_candidate, total_retries, fallback_used, None
                    else:
                        last_error = f"Gemini fallback failed: empty response from API ({model_candidate})"
                except APIError as e:
                    err_str = str(e)
                    last_error = f"Gemini fallback failed: API error ({e})"
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        if attempt == 0:
                            wait_time = 2.5
                            try:
                                import re
                                match = re.search(r"retry in (\d+\.?\d*)s", err_str, re.IGNORECASE)
                                if match:
                                    wait_time = float(match.group(1)) + 0.5
                            except Exception:
                                pass
                            logger.info(f"Gemini model '{model_candidate}' hit 429 quota. Retrying after {wait_time:.1f}s backoff...")
                            time.sleep(min(wait_time, 5.0))
                            continue  # Retry once after backoff
                        else:
                            logger.info(f"Gemini model '{model_candidate}' exhausted after retry. Falling back to next model...")
                            break  # Move to next candidate model
                    elif "404" in err_str or "NOT_FOUND" in err_str:
                        logger.info(f"Gemini model '{model_candidate}' not found (404). Falling back...")
                        break  # Move to next candidate model
                    else:
                        logger.warning(f"Gemini API error on model '{model_candidate}': {e}")
                        break
                except Exception as e:
                    last_error = f"Gemini fallback failed: {e}"
                    logger.warning(f"Unexpected error calling Gemini model '{model_candidate}': {e}")
                    break

        return None, primary_model, total_retries, True, last_error

    def _sanitize_json_response(self, text: str) -> str:
        """Sanitize Gemini raw response text to extract the first complete JSON object.

        Args:
            text: Raw response string from Gemini API.

        Returns:
            str: Cleaned JSON object string ready for json.loads().
        """
        if not text:
            return ""

        cleaned = text.strip()

        # 1. Strip markdown code block wrapping if present
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # 2. Extract first complete JSON object using bracket balance matching
        start_idx = cleaned.find("{")
        if start_idx != -1:
            depth = 0
            in_string = False
            escape = False
            end_idx = -1
            for i in range(start_idx, len(cleaned)):
                char = cleaned[i]
                if escape:
                    escape = False
                    continue
                if char == "\\" and in_string:
                    escape = True
                    continue
                if char == '"':
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            end_idx = i + 1
                            break
            if end_idx != -1:
                cleaned = cleaned[start_idx:end_idx]
            elif depth > 0:
                repaired = cleaned[start_idx:].rstrip()
                if in_string:
                    repaired += '"'
                repaired += "}" * depth
                cleaned = repaired

        return cleaned

    def _is_enrichment_required(self, alert: ParsedAlert) -> bool:
        """Check if any of raw_hazard, raw_severity, or raw_location are missing."""
        return not alert.raw_hazard or not alert.raw_severity or not alert.raw_location

    def _build_prompt(self, text: str) -> str:
        """Build structured prompt using PROMPT_VERSION with explicit few-shot examples.

        Args:
            text: Original alert raw text.

        Returns:
            str: Structured prompt string.
        """
        return (
            f"You are a disaster alert information extraction engine (Prompt Version: {PROMPT_VERSION}).\n"
            "Extract disaster information from the provided text into JSON format.\n\n"
            "Return a JSON object containing EXACTLY the following 8 keys:\n"
            "- raw_hazard: raw hazard or event category (e.g. 'flood warning', 'flash flood', 'cyclone', 'landslide', 'heatwave', 'wildfire', 'lightning', 'earthquake'). Infer hazard type when strongly implied by wording (e.g. heavy rainfall or flood warning -> 'flood warning' or 'flood'; cyclone -> 'cyclone'; landslide -> 'landslide'; heatwave -> 'heatwave'; forest fire -> 'wildfire').\n"
            "- raw_severity: raw severity or alert level keyword ('Extreme', 'Severe', 'Moderate', 'Minor', or null if unknown). Infer from tone or explicit terms (e.g. warning/flash flood/cyclone -> 'Severe' or 'Extreme'; watch/risk -> 'Moderate' or 'Severe').\n"
            "- raw_urgency: raw urgency keyword ('Immediate', 'Expected', 'Future', 'Past', or null if unknown). Infer from temporal context or warning language (e.g. 'tonight' or 'flash flood' -> 'Immediate'; 'tomorrow' or 'warning' -> 'Expected'; 'this weekend' -> 'Expected' or 'Future').\n"
            "- raw_certainty: raw certainty keyword ('Observed', 'Likely', 'Possible', or null if unknown). Infer from confidence tone (e.g. reported/occurring -> 'Observed'; warning/expected -> 'Likely'; risk/watch/potential -> 'Possible').\n"
            "- raw_location: raw location or area name mentioned (e.g. 'Devapur', 'Chennai', 'Munnar', 'Mysore', 'Bengaluru', 'Ooty') or null if missing.\n"
            "- raw_start_time: raw start time or validity start text (e.g. 'tomorrow morning', 'tonight', 'this weekend') or null if missing.\n"
            "- raw_end_time: raw end time or validity end text or null if missing.\n"
            "- raw_action: raw recommended action or protective instruction sentence/clause (e.g. 'Residents should avoid flooded roads') or null if missing.\n\n"
            "FEW-SHOT EXAMPLES:\n\n"
            "Example 1 (Flood):\n"
            'Input: "Heavy rainfall warning for Devapur tomorrow morning. Residents should avoid flooded roads."\n'
            'Output: {"raw_hazard": "flood warning", "raw_severity": "Severe", "raw_urgency": "Expected", "raw_certainty": "Likely", "raw_location": "Devapur", "raw_start_time": "tomorrow morning", "raw_end_time": null, "raw_action": "Residents should avoid flooded roads"}\n\n'
            "Example 2 (Cyclone):\n"
            'Input: "Cyclone expected near Chennai tonight."\n'
            'Output: {"raw_hazard": "cyclone", "raw_severity": "Severe", "raw_urgency": "Immediate", "raw_certainty": "Likely", "raw_location": "Chennai", "raw_start_time": "tonight", "raw_end_time": null, "raw_action": null}\n\n'
            "Example 3 (Landslide):\n"
            'Input: "Landslide risk in Munnar after continuous rainfall."\n'
            'Output: {"raw_hazard": "landslide", "raw_severity": "Moderate", "raw_urgency": "Expected", "raw_certainty": "Possible", "raw_location": "Munnar", "raw_start_time": null, "raw_end_time": null, "raw_action": null}\n\n'
            "Example 4 (Flash Flood):\n"
            'Input: "Flash flood warning for Mysore."\n'
            'Output: {"raw_hazard": "flash flood", "raw_severity": "Severe", "raw_urgency": "Immediate", "raw_certainty": "Likely", "raw_location": "Mysore", "raw_start_time": null, "raw_end_time": null, "raw_action": null}\n\n'
            "Example 5 (Heatwave):\n"
            'Input: "Heatwave warning for Bengaluru this weekend."\n'
            'Output: {"raw_hazard": "heatwave", "raw_severity": "Severe", "raw_urgency": "Expected", "raw_certainty": "Likely", "raw_location": "Bengaluru", "raw_start_time": "this weekend", "raw_end_time": null, "raw_action": null}\n\n'
            "Example 6 (Wildfire / Forest Fire):\n"
            'Input: "Forest fire spreading near Ooty."\n'
            'Output: {"raw_hazard": "wildfire", "raw_severity": "Severe", "raw_urgency": "Immediate", "raw_certainty": "Observed", "raw_location": "Ooty", "raw_start_time": null, "raw_end_time": null, "raw_action": null}\n\n'
            "STRICT RULES:\n"
            "1. Return STRICT JSON ONLY. No markdown wrapping (no ```json), no explanatory text, no prose.\n"
            "2. Do NOT add any keys other than the 8 keys listed above.\n"
            "3. Do NOT hallucinate or invent facts. Never fabricate alert IDs, timestamps, or administrative codes.\n"
            "4. Prefer conservative semantic inference ONLY when strongly implied by plain English text.\n"
            "5. If a field cannot be identified or inferred with confidence, set its value to null.\n\n"
            f"Input Text: {text}"
        )

    def _merge_extracted_fields(self, alert: ParsedAlert, data: Dict[str, Any]) -> List[str]:
        """Merge extracted fields into ParsedAlert preserving existing parser values."""
        populated = []
        if not alert.raw_hazard and data.get("raw_hazard"):
            alert.raw_hazard = str(data["raw_hazard"])
            populated.append("raw_hazard")

        if not alert.raw_severity and data.get("raw_severity"):
            alert.raw_severity = str(data["raw_severity"])
            populated.append("raw_severity")

        if not alert.raw_urgency and data.get("raw_urgency"):
            alert.raw_urgency = str(data["raw_urgency"])
            populated.append("raw_urgency")

        if not alert.raw_certainty and data.get("raw_certainty"):
            alert.raw_certainty = str(data["raw_certainty"])
            populated.append("raw_certainty")

        if not alert.raw_location and data.get("raw_location"):
            alert.raw_location = str(data["raw_location"])
            populated.append("raw_location")

        if not alert.raw_start_time and data.get("raw_start_time"):
            alert.raw_start_time = str(data["raw_start_time"])
            populated.append("raw_start_time")

        if not alert.raw_end_time and data.get("raw_end_time"):
            alert.raw_end_time = str(data["raw_end_time"])
            populated.append("raw_end_time")

        if not alert.raw_action and data.get("raw_action"):
            alert.raw_action = str(data["raw_action"])
            populated.append("raw_action")

        return populated


