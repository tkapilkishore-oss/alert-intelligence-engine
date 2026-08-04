"""Unit and integration test suite for Natural Language Entry Layer (Stage 12)."""

from unittest.mock import MagicMock, patch
import pytest

from src.nlp_processor import NaturalLanguageProcessor
from src.pipeline import AlertPipeline
from src.schema import NormalizedAlert, ParsedAlert


def test_natural_language_conversion():
    """Verify NaturalLanguageProcessor converts free-form text into a valid ParsedAlert."""
    processor = NaturalLanguageProcessor()
    text = "Heavy rainfall is expected tomorrow morning in Devapur. People should avoid flooded roads."
    alert = processor.process(text)

    assert isinstance(alert, ParsedAlert)
    assert alert.source == "Natural Language Entry Layer"
    assert alert.source_format == "plaintext"
    assert alert.raw_payload == {"original_text": text}
    assert alert.parse_warnings == []


def test_parsed_alert_generation():
    """Verify ParsedAlert fields remain None by default preserving parser philosophy."""
    processor = NaturalLanguageProcessor()
    alert = processor.process("Lightning reported near Vanasthal.")

    assert alert.raw_hazard is None
    assert alert.raw_severity is None
    assert alert.raw_urgency is None
    assert alert.raw_certainty is None
    assert alert.raw_location is None
    assert alert.raw_start_time is None
    assert alert.raw_end_time is None
    assert alert.raw_action is None


def test_gemini_integration():
    """Verify pipeline GeminiExtractor integration with NaturalLanguageProcessor outputs."""
    processor = NaturalLanguageProcessor()
    text = "Heatwave expected across Suryanagar this afternoon."
    parsed = processor.process(text)

    mock_gemini_response = {
        "raw_hazard": "heatwave",
        "raw_severity": "Severe",
        "raw_location": "Suryanagar",
        "raw_start_time": "this afternoon",
        "raw_end_time": None,
        "raw_action": None,
    }

    pipeline = AlertPipeline()
    with patch.object(pipeline._gemini_extractor, "_build_prompt", return_value="test prompt"):
        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_response = MagicMock()
            mock_response.text = '{"raw_hazard": "heatwave", "raw_severity": "Severe", "raw_location": "Suryanagar"}'
            mock_client.models.generate_content.return_value = mock_response

            normalized_list = pipeline.process_natural_language(text)
            assert len(normalized_list) == 1
            assert isinstance(normalized_list[0], NormalizedAlert)
            assert normalized_list[0].hazard_type == "heatwave"
            assert normalized_list[0].severity == "Severe"


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


def test_pipeline_integration():
    """Verify AlertPipeline.process_natural_language end-to-end workflow."""
    pipeline = AlertPipeline()
    with patch.object(pipeline._gemini_extractor, "enrich") as mock_enrich:
        # Mock enrichment to return populated ParsedAlert
        def enrich_side_effect(alert):
            enriched = alert.model_copy(deep=True)
            enriched.raw_hazard = "flood"
            enriched.raw_severity = "Severe"
            enriched.raw_location = "Devapur"
            enriched.raw_action = "avoid flooded roads"
            return enriched

        mock_enrich.side_effect = enrich_side_effect

        normalized_list = pipeline.process_natural_language(
            "Heavy rainfall is expected tomorrow morning in Devapur. People should avoid flooded roads."
        )

        assert len(normalized_list) == 1
        norm = normalized_list[0]
        assert norm.hazard_type == "flood"
        assert norm.severity == "Severe"
        assert norm.location_name == "Devapur"
        assert norm.source == "Natural Language Entry Layer"


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
