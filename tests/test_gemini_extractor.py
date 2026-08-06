"""Unit test suite for Stage 6 Gemini Fallback Engine."""

import json
from unittest.mock import MagicMock, patch
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from google.genai.errors import APIError

from src.gemini_extractor import PROMPT_VERSION, GeminiExtractor
from src.schema import ParsedAlert


@pytest.fixture
def sample_incomplete_alert() -> ParsedAlert:
    """Fixture returning an incomplete ParsedAlert missing severity and location."""
    return ParsedAlert(
        raw_hazard="heavy rain",
        raw_severity=None,
        raw_location=None,
        raw_start_time=None,
        raw_end_time=None,
        raw_action=None,
        source="Plaintext Alert System",
        source_format="plaintext",
        raw_payload={
            "original_text": "Malformed alert: heavy rain maybe somewhere soon",
            "detected_pattern": "free_text",
        },
        parse_warnings=["missing severity", "missing location", "missing start_time"],
    )


@pytest.fixture
def sample_complete_alert() -> ParsedAlert:
    """Fixture returning a complete ParsedAlert with hazard, severity, and location present."""
    return ParsedAlert(
        raw_hazard="flood warning",
        raw_severity="Severe",
        raw_location="Devapur",
        raw_start_time="2025-07-16 08:00",
        raw_end_time=None,
        raw_action="avoid river-side roads",
        source="ALERT PT-001",
        source_format="plaintext",
        raw_payload={"original_text": "ALERT PT-001 | Devapur | Severe flood warning"},
        parse_warnings=[],
    )


def test_prompt_version_constant():
    """Verify PROMPT_VERSION constant is defined as 'v2'."""
    assert PROMPT_VERSION == "v2"


def test_gemini_skipped_when_unnecessary(sample_complete_alert):
    """Verify Gemini API is not invoked when required fields (hazard, severity, location) are present."""
    extractor = GeminiExtractor(api_key="fake_key")
    with patch("google.genai.Client") as mock_client_cls:
        result = extractor.enrich(sample_complete_alert)
        mock_client_cls.assert_not_called()
        assert result.raw_hazard == "flood warning"
        assert result.raw_severity == "Severe"
        assert result.raw_location == "Devapur"
        assert result.parse_warnings == []


def test_gemini_input_immutability(sample_incomplete_alert):
    """Verify enrich() leaves the original ParsedAlert untouched and returns a deep copy."""
    extractor = GeminiExtractor(api_key="fake_key")
    gemini_json = json.dumps(
        {
            "raw_hazard": "heavy rain",
            "raw_severity": "Moderate",
            "raw_location": "Nirmala Block 1",
            "raw_start_time": "2025-07-16 10:00",
            "raw_end_time": None,
            "raw_action": "Stay indoors",
        }
    )

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = gemini_json
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        original_copy = sample_incomplete_alert.model_copy(deep=True)
        enriched = extractor.enrich(sample_incomplete_alert)

        # Original alert MUST remain untouched
        assert sample_incomplete_alert.raw_severity is None
        assert sample_incomplete_alert.raw_location is None
        assert sample_incomplete_alert.parse_warnings == original_copy.parse_warnings

        # Enriched alert contains merged values
        assert enriched is not sample_incomplete_alert
        assert enriched.raw_severity == "Moderate"
        assert enriched.raw_location == "Nirmala Block 1"


def test_gemini_enrichment_success(sample_incomplete_alert):
    """Verify successful field enrichment from mocked Gemini API response."""
    extractor = GeminiExtractor(api_key="fake_key")
    gemini_json = json.dumps(
        {
            "raw_hazard": "heavy rain",
            "raw_severity": "Moderate",
            "raw_location": "Vanasthal",
            "raw_start_time": "15 Jul 2025 18:00",
            "raw_end_time": "15 Jul 2025 22:00",
            "raw_action": "Stay indoors",
        }
    )

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = gemini_json
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        enriched = extractor.enrich(sample_incomplete_alert)

        assert enriched.raw_hazard == "heavy rain"
        assert enriched.raw_severity == "Moderate"
        assert enriched.raw_location == "Vanasthal"
        assert enriched.raw_start_time == "15 Jul 2025 18:00"
        assert enriched.raw_end_time == "15 Jul 2025 22:00"
        assert enriched.raw_action == "Stay indoors"


def test_gemini_merge_policy_parser_wins(sample_incomplete_alert):
    """Verify deterministic parser fields are never overwritten by Gemini response."""
    sample_incomplete_alert.raw_hazard = "Deterministic Hazard"
    sample_incomplete_alert.raw_severity = None
    sample_incomplete_alert.raw_location = None

    extractor = GeminiExtractor(api_key="fake_key")
    gemini_json = json.dumps(
        {
            "raw_hazard": "Gemini Hazard Overwrite",
            "raw_severity": "Severe",
            "raw_location": "Suryanagar",
            "raw_start_time": None,
            "raw_end_time": None,
            "raw_action": None,
        }
    )

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = gemini_json
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        enriched = extractor.enrich(sample_incomplete_alert)

        # Parser value preserved!
        assert enriched.raw_hazard == "Deterministic Hazard"
        assert enriched.raw_severity == "Severe"
        assert enriched.raw_location == "Suryanagar"


def test_gemini_unexpected_json_keys_rejection(sample_incomplete_alert):
    """Verify response containing unexpected keys is rejected and parse_warning appended."""
    extractor = GeminiExtractor(api_key="fake_key")
    gemini_json_with_extra = json.dumps(
        {
            "raw_hazard": "heavy rain",
            "raw_severity": "Moderate",
            "raw_location": "Vanasthal",
            "raw_start_time": None,
            "raw_end_time": None,
            "raw_action": None,
            "extra_unauthorized_key": "hallucinated data",
        }
    )

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = gemini_json_with_extra
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        enriched = extractor.enrich(sample_incomplete_alert)

        # Output discarded, original fields kept
        assert enriched.raw_severity is None
        assert enriched.raw_location is None
        assert any(
            "unexpected keys in JSON response" in w for w in enriched.parse_warnings
        )


def test_gemini_missing_api_key(sample_incomplete_alert):
    """Verify missing API key skips Gemini call and appends parse_warning."""
    extractor = GeminiExtractor(api_key="")
    enriched = extractor.enrich(sample_incomplete_alert)
    assert any("GEMINI_API_KEY missing" in w for w in enriched.parse_warnings)


def test_gemini_invalid_json_handling(sample_incomplete_alert):
    """Verify invalid non-JSON text response appends parse_warning and returns safely."""
    extractor = GeminiExtractor(api_key="fake_key")
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "NOT VALID JSON EXPLANATION"
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        enriched = extractor.enrich(sample_incomplete_alert)
        assert any("invalid JSON response" in w for w in enriched.parse_warnings)
        assert enriched.raw_severity is None


def test_gemini_empty_response_handling(sample_incomplete_alert):
    """Verify empty response text appends parse_warning and returns safely."""
    extractor = GeminiExtractor(api_key="fake_key")
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        enriched = extractor.enrich(sample_incomplete_alert)
        assert any("empty response from API" in w for w in enriched.parse_warnings)


def test_gemini_api_exception_handling(sample_incomplete_alert):
    """Verify APIError exception appends parse_warning and returns safely."""
    extractor = GeminiExtractor(api_key="fake_key")
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = APIError(
            429, {"message": "Quota exceeded"}
        )
        mock_client_cls.return_value = mock_client

        enriched = extractor.enrich(sample_incomplete_alert)
        assert any("API error" in w for w in enriched.parse_warnings)



def test_gemini_timeout_exception_handling(sample_incomplete_alert):
    """Verify TimeoutError appends parse_warning and returns safely."""
    extractor = GeminiExtractor(api_key="fake_key")
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = TimeoutError("Request timed out")
        mock_client_cls.return_value = mock_client

        enriched = extractor.enrich(sample_incomplete_alert)
        assert any("Request timed out" in w for w in enriched.parse_warnings)


def test_gemini_client_initialization_with_api_key():
    """Verify GeminiExtractor initializes genai.Client(api_key=...) with configured environment or key."""
    aq_key = "AQ.TEST_DUMMY_KEY_FOR_UNIT_TESTING_12345"
    ext_aq = GeminiExtractor(api_key=aq_key)
    assert ext_aq._api_key == aq_key


def test_sanitize_json_response_extra_data():
    """Verify _sanitize_json_response recovers valid JSON when surrounded by extra data or markdown fences."""
    extractor = GeminiExtractor(api_key="fake_key")
    raw_with_extra = (
        "Here is the result:\n"
        '{"raw_hazard": "flood", "raw_severity": "Severe", "raw_urgency": "Expected", "raw_certainty": "Likely", "raw_location": "Devapur", "raw_start_time": null, "raw_end_time": null, "raw_action": "Residents should avoid flooded roads"}\n'
        "Extra data: line 11 column 1 (char 271)"
    )
    sanitized = extractor._sanitize_json_response(raw_with_extra)
    data = json.loads(sanitized)
    assert data["raw_hazard"] == "flood"
    assert data["raw_location"] == "Devapur"


def test_sanitize_json_response_unclosed():
    """Verify _sanitize_json_response repairs unclosed/truncated JSON objects missing trailing closing brace."""
    extractor = GeminiExtractor(api_key="fake_key")
    raw_unclosed = (
        "{\n"
        '  "raw_hazard": "flood warning",\n'
        '  "raw_severity": "Severe",\n'
        '  "raw_urgency": "Expected",\n'
        '  "raw_certainty": "Likely",\n'
        '  "raw_location": "Devapur",\n'
        '  "raw_start_time": "tomorrow morning",\n'
        '  "raw_end_time": null,\n'
        '  "raw_action": "Residents should avoid flooded roads"'
    )
    sanitized = extractor._sanitize_json_response(raw_unclosed)
    data = json.loads(sanitized)
    assert data["raw_hazard"] == "flood warning"
    assert data["raw_location"] == "Devapur"
