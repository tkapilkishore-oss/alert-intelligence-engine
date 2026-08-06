"""Gemini Fallback Engine module for Alert Intelligence Engine."""

import json
import os
from typing import Any, Dict, Optional, Set

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

from src.logger import get_logger
from src.schema import ParsedAlert

logger = get_logger(__name__)

PROMPT_VERSION: str = "v1"
DEFAULT_GEMINI_MODEL: str = "gemini-2.5-flash"

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
        model_name: str = DEFAULT_GEMINI_MODEL,
    ) -> None:
        """Initialize GeminiExtractor with optional API key and model name.

        Args:
            api_key: Optional API key override. Reads from .env GEMINI_API_KEY by default.
            model_name: Gemini model identifier to query.
        """
        load_dotenv()
        if api_key is None:
            self._api_key = os.getenv("GEMINI_API_KEY")
        else:
            self._api_key = api_key
        self._model_name = model_name


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

        try:
            client = genai.Client(api_key=self._api_key)
            response = client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            if not response or not response.text:
                enriched_alert.parse_warnings.append(
                    "Gemini fallback failed: empty response from API"
                )
                return enriched_alert

            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```"):
                lines = cleaned_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned_text = "\n".join(lines).strip()

            extracted_data = json.loads(cleaned_text)

            if not isinstance(extracted_data, dict):
                enriched_alert.parse_warnings.append(
                    "Gemini fallback failed: response JSON is not an object"
                )
                return enriched_alert

            # Validate that returned JSON contains ONLY allowed keys.
            extra_keys = set(extracted_data.keys()) - ALLOWED_GEMINI_KEYS
            if extra_keys:
                warning_msg = (
                    f"Gemini fallback rejected: unexpected keys in JSON response "
                    f"({', '.join(sorted(extra_keys))})"
                )
                enriched_alert.parse_warnings.append(warning_msg)
                logger.warning(warning_msg)
                return enriched_alert

            # Merge policy: Parser always wins, Gemini only fills missing fields.
            self._merge_extracted_fields(enriched_alert, extracted_data)

        except APIError as e:
            msg = f"Gemini fallback failed: API error ({e})"
            enriched_alert.parse_warnings.append(msg)
            logger.warning(msg)
        except json.JSONDecodeError as e:
            msg = f"Gemini fallback failed: invalid JSON response ({e})"
            enriched_alert.parse_warnings.append(msg)
            logger.warning(msg)
        except Exception as e:
            msg = f"Gemini fallback failed: {e}"
            enriched_alert.parse_warnings.append(msg)
            logger.warning(msg)

        return enriched_alert

    def _is_enrichment_required(self, alert: ParsedAlert) -> bool:
        """Check if any of raw_hazard, raw_severity, or raw_location are missing."""
        return not alert.raw_hazard or not alert.raw_severity or not alert.raw_location

    def _build_prompt(self, text: str) -> str:
        """Build structured prompt using PROMPT_VERSION with few-shot examples.

        Args:
            text: Original alert raw text.

        Returns:
            str: Structured prompt string.
        """
        return (
            f"You are a disaster alert information extraction engine (Prompt Version: {PROMPT_VERSION}).\n"
            "Extract disaster information from the provided text into JSON format.\n\n"
            "Return a JSON object containing EXACTLY the following 8 keys:\n"
            "- raw_hazard: raw hazard or event category (e.g. 'flood warning', 'flash flood', 'cyclone', 'landslide', 'heatwave', 'lightning', 'earthquake'). Infer hazard type when strongly implied by wording (e.g. heavy rainfall or flood warning -> 'flood warning' or 'flood'; cyclone -> 'cyclone'; landslide -> 'landslide'; heatwave -> 'heatwave').\n"
            "- raw_severity: raw severity or alert level keyword ('Extreme', 'Severe', 'Moderate', 'Minor', or null if unknown). Infer from tone or explicit terms (e.g. warning/flash flood/cyclone -> 'Severe' or 'Extreme'; watch/risk -> 'Moderate' or 'Severe').\n"
            "- raw_urgency: raw urgency keyword ('Immediate', 'Expected', 'Future', 'Past', or null if unknown). Infer from temporal context or warning language (e.g. 'tonight' or 'flash flood' -> 'Immediate'; 'tomorrow' or 'warning' -> 'Expected'; 'this weekend' -> 'Expected' or 'Future').\n"
            "- raw_certainty: raw certainty keyword ('Observed', 'Likely', 'Possible', or null if unknown). Infer from confidence tone (e.g. reported/occurring -> 'Observed'; warning/expected -> 'Likely'; risk/watch/potential -> 'Possible').\n"
            "- raw_location: raw location or area name mentioned (e.g. 'Devapur', 'Chennai', 'Munnar', 'Mysore', 'Bengaluru') or null if missing.\n"
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
            "STRICT RULES:\n"
            "1. Return STRICT JSON ONLY. No markdown wrapping (no ```json), no explanatory text.\n"
            "2. Do NOT add any keys other than the 8 keys listed above.\n"
            "3. Do NOT hallucinate or invent facts. Never fabricate alert IDs, timestamps, or administrative codes.\n"
            "4. Prefer conservative semantic inference ONLY when strongly implied by plain English text.\n"
            "5. If a field cannot be identified or inferred with confidence, set its value to null.\n\n"
            f"Input Text: {text}"
        )

    def _merge_extracted_fields(self, alert: ParsedAlert, data: Dict[str, Any]) -> None:
        """Merge extracted fields into ParsedAlert preserving existing parser values."""
        if not alert.raw_hazard and data.get("raw_hazard"):
            alert.raw_hazard = str(data["raw_hazard"])

        if not alert.raw_severity and data.get("raw_severity"):
            alert.raw_severity = str(data["raw_severity"])

        if not alert.raw_urgency and data.get("raw_urgency"):
            alert.raw_urgency = str(data["raw_urgency"])

        if not alert.raw_certainty and data.get("raw_certainty"):
            alert.raw_certainty = str(data["raw_certainty"])

        if not alert.raw_location and data.get("raw_location"):
            alert.raw_location = str(data["raw_location"])

        if not alert.raw_start_time and data.get("raw_start_time"):
            alert.raw_start_time = str(data["raw_start_time"])

        if not alert.raw_end_time and data.get("raw_end_time"):
            alert.raw_end_time = str(data["raw_end_time"])

        if not alert.raw_action and data.get("raw_action"):
            alert.raw_action = str(data["raw_action"])

