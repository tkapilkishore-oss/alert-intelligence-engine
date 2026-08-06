"""Unit and integration test suite for Natural Language Entry Layer (Stage 12)."""

import json
from unittest.mock import MagicMock, patch
import pytest

from src.nlp_processor import NaturalLanguageProcessor
from src.pipeline import AlertPipeline
from src.schema import NormalizedAlert, ParsedAlert


def test_natural_language_conversion():
    """Verify NaturalLanguageProcessor converts free-form text into a valid ParsedAlert."""
    processor = NaturalLanguageProcessor()
    text = "Heavy rainfall is expected tomorrow morning in Devapur. People should avoid flooded roads."

    with patch.object(processor._gemini_extractor, "enrich", side_effect=lambda a: a.model_copy(deep=True)) as mock_enrich:
        alert = processor.process(text)

        mock_enrich.assert_called_once()
        assert isinstance(alert, ParsedAlert)
        assert alert.source == "Natural Language Entry Layer"
        assert alert.source_format == "plaintext"
        assert alert.raw_payload == {"original_text": text, "_nlp_processed": True}
        assert alert.parse_warnings == []


def test_parsed_alert_generation():
    """Verify ParsedAlert fields remain None when enrichment returns no values."""
    processor = NaturalLanguageProcessor()

    with patch.object(processor._gemini_extractor, "enrich", side_effect=lambda a: a.model_copy(deep=True)):
        alert = processor.process("Lightning reported near Vanasthal.")

        assert alert.raw_hazard is None
        assert alert.raw_severity is None
        assert alert.raw_urgency is None
        assert alert.raw_certainty is None
        assert alert.raw_location is None
        assert alert.raw_start_time is None
        assert alert.raw_end_time is None
        assert alert.raw_action is None


def test_single_gemini_call_verification():
    """Verify that AlertPipeline.process_natural_language invokes Gemini API exactly once."""
    pipeline = AlertPipeline()
    text = "Heavy rainfall warning for Devapur tomorrow morning. Residents should avoid flooded roads."

    mock_gemini_json = json.dumps({
        "raw_hazard": "flood warning",
        "raw_severity": "Severe",
        "raw_urgency": "Expected",
        "raw_certainty": "Likely",
        "raw_location": "Devapur",
        "raw_start_time": "tomorrow morning",
        "raw_end_time": None,
        "raw_action": "Residents should avoid flooded roads"
    })

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = mock_gemini_json
        mock_client.models.generate_content.return_value = mock_response

        normalized_list = pipeline.process_natural_language(text)

        # STRICT VERIFICATION: generate_content invoked EXACTLY ONCE
        assert mock_client.models.generate_content.call_count == 1

        assert len(normalized_list) == 1
        norm = normalized_list[0]
        assert norm.hazard_type == "flood"
        assert norm.severity == "Severe"
        assert norm.urgency == "Expected"
        assert norm.certainty == "Likely"
        assert norm.location_name == "Devapur"
        assert norm.location_id == "DIST-03"
        assert norm.recommended_action == "Residents should avoid flooded roads"


@pytest.mark.parametrize(
    "text,mock_payload,expected_hazard,expected_severity,expected_urgency,expected_certainty,expected_location,expected_action",
    [
        (
            "Heavy rainfall warning for Devapur tomorrow morning. Residents should avoid flooded roads.",
            {
                "raw_hazard": "flood warning",
                "raw_severity": "Severe",
                "raw_urgency": "Expected",
                "raw_certainty": "Likely",
                "raw_location": "Devapur",
                "raw_start_time": "tomorrow morning",
                "raw_end_time": None,
                "raw_action": "Residents should avoid flooded roads",
            },
            "flood",
            "Severe",
            "Expected",
            "Likely",
            "Devapur",
            "Residents should avoid flooded roads",
        ),
        (
            "Cyclone expected near Chennai tonight.",
            {
                "raw_hazard": "cyclone",
                "raw_severity": "Severe",
                "raw_urgency": "Immediate",
                "raw_certainty": "Likely",
                "raw_location": "Chennai",
                "raw_start_time": "tonight",
                "raw_end_time": None,
                "raw_action": None,
            },
            "cyclone",
            "Severe",
            "Immediate",
            "Likely",
            "Chennai",
            "No action specified",
        ),
        (
            "Landslide risk in Munnar after continuous rainfall.",
            {
                "raw_hazard": "landslide",
                "raw_severity": "Moderate",
                "raw_urgency": "Expected",
                "raw_certainty": "Possible",
                "raw_location": "Munnar",
                "raw_start_time": None,
                "raw_end_time": null if False else None,
                "raw_action": None,
            },
            "landslide",
            "Moderate",
            "Expected",
            "Possible",
            "Munnar",
            "No action specified",
        ),
        (
            "Flash flood warning for Mysore.",
            {
                "raw_hazard": "flash flood",
                "raw_severity": "Severe",
                "raw_urgency": "Immediate",
                "raw_certainty": "Likely",
                "raw_location": "Mysore",
                "raw_start_time": None,
                "raw_end_time": None,
                "raw_action": None,
            },
            "flood",
            "Severe",
            "Immediate",
            "Likely",
            "Mysore",
            "No action specified",
        ),
        (
            "Heatwave warning for Bengaluru this weekend.",
            {
                "raw_hazard": "heatwave",
                "raw_severity": "Severe",
                "raw_urgency": "Expected",
                "raw_certainty": "Likely",
                "raw_location": "Bengaluru",
                "raw_start_time": "this weekend",
                "raw_end_time": None,
                "raw_action": None,
            },
            "heatwave",
            "Severe",
            "Expected",
            "Likely",
            "Bengaluru",
            "No action specified",
        ),
    ],
)
def test_natural_language_examples_verification(
    text,
    mock_payload,
    expected_hazard,
    expected_severity,
    expected_urgency,
    expected_certainty,
    expected_location,
    expected_action,
):
    """Verify natural language examples extract rich ParsedAlert fields and correct NormalizedAlert output."""
    pipeline = AlertPipeline()

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_payload)
        mock_client.models.generate_content.return_value = mock_response

        normalized_list = pipeline.process_natural_language(text)

        assert mock_client.models.generate_content.call_count == 1
        assert len(normalized_list) == 1
        norm = normalized_list[0]
        assert norm.hazard_type == expected_hazard
        assert norm.severity == expected_severity
        assert norm.urgency == expected_urgency
        assert norm.certainty == expected_certainty
        assert norm.location_name == expected_location
        assert norm.recommended_action == expected_action


def test_warning_preservation():
    """Verify warnings generated during Natural Language Processing are preserved."""
    processor = NaturalLanguageProcessor()
    alert = processor.process("   ")
    assert len(alert.parse_warnings) == 1
    assert "Empty or whitespace natural language input text" in alert.parse_warnings[0]


def test_invalid_input():
    """Verify invalid (non-string) input generates parse warning without crashing."""
    processor = NaturalLanguageProcessor()
    alert = processor.process(12345)

    assert isinstance(alert, ParsedAlert)
    assert len(alert.parse_warnings) == 1
    assert "Invalid input type: expected str" in alert.parse_warnings[0]


def test_empty_input():
    """Verify empty string input generates warning and produces valid empty ParsedAlert."""
    processor = NaturalLanguageProcessor()
    alert = processor.process("")

    assert isinstance(alert, ParsedAlert)
    assert len(alert.parse_warnings) == 1
    assert "Empty or whitespace natural language input text" in alert.parse_warnings[0]


def test_input_immutability():
    """Verify natural language processing never mutates input text string or parameters."""
    text = "Heavy rainfall in Devapur."
    original_text = str(text)

    pipeline = AlertPipeline()
    with patch.object(pipeline._gemini_extractor, "enrich", side_effect=lambda a: a.model_copy(deep=True)):
        pipeline.process_natural_language(text)

    assert text == original_text


def test_regression_safety():
    """Verify adding Natural Language Layer causes zero regression to standard pipeline processing."""
    pipeline = AlertPipeline()
    raw_json = [
        {
            "alert_id": "JSON-101",
            "source_org": "TestOrg",
            "hazard": "cyclone",
            "severity_level": "Extreme",
            "urgency": "Immediate",
            "certainty": "Observed",
            "affected_area": "Kakinada",
            "location_code": "DIST-01",
            "issuance_time": "2025-07-15T08:00:00+05:30",
            "instruction": "Evacuate coastal area",
        }
    ]

    normalized_json = pipeline.process(raw_json, "json")
    assert len(normalized_json) == 1
    assert normalized_json[0].hazard_type == "cyclone"
    assert normalized_json[0].source_format == "json"

