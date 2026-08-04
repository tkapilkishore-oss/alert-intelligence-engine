"""End-to-End System Verification test suite for Alert Intelligence Engine (Stage 11)."""

import json
from unittest.mock import MagicMock, patch
import pytest

from src.pipeline import AlertPipeline
from src.schema import NormalizedAlert


def test_e2e_json_dataset() -> None:
    """Scenario 1: Verify end-to-end processing of the provided raw JSON dataset."""
    pipeline = AlertPipeline()
    with open("data/raw_alerts_json.json", "r", encoding="utf-8") as f:
        raw_json_data = json.load(f)

    results = pipeline.process(raw_json_data, "json")

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(alert, NormalizedAlert) for alert in results)
    # Check that alert IDs and hazards are extracted and normalized
    alert_ids = [alert.alert_id for alert in results]
    assert "JSON-001" in alert_ids
    assert "JSON-002" in alert_ids


def test_e2e_cap_xml_dataset() -> None:
    """Scenario 2: Verify end-to-end processing of the provided raw CAP XML dataset."""
    pipeline = AlertPipeline()
    with open("data/raw_alerts_cap.xml", "r", encoding="utf-8") as f:
        raw_cap_data = f.read()

    results = pipeline.process(raw_cap_data, "cap_xml")

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(alert, NormalizedAlert) for alert in results)
    assert any(alert.hazard_type in ["cyclone", "flood", "heatwave", "landslide"] for alert in results)


def test_e2e_rss_dataset() -> None:
    """Scenario 3: Verify end-to-end processing of the provided raw RSS XML dataset."""
    pipeline = AlertPipeline()
    with open("data/raw_alerts_rss.xml", "r", encoding="utf-8") as f:
        raw_rss_data = f.read()

    results = pipeline.process(raw_rss_data, "rss")

    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(alert, NormalizedAlert) for alert in results)


def test_e2e_plaintext_deterministic() -> None:
    """Scenario 4: Verify end-to-end processing of deterministic Plaintext dataset."""
    pipeline = AlertPipeline()
    raw_text = "ALERT PT-001 | Devapur | Severe flood warning | starts 2025-07-16 08:00 | avoid river-side roads"

    results = pipeline.process(raw_text, "plaintext")

    assert isinstance(results, list)
    assert len(results) == 1
    alert = results[0]
    assert isinstance(alert, NormalizedAlert)
    assert alert.hazard_type == "flood"
    assert alert.severity == "Severe"
    assert alert.location_name == "Devapur"
    assert alert.recommended_action == "avoid river-side roads"


def test_e2e_plaintext_gemini_fallback() -> None:
    """Scenario 5: Verify Plaintext processing requiring Gemini fallback enrichment."""
    pipeline = AlertPipeline()
    incomplete_text = "Malformed alert: heavy rain maybe somewhere soon"

    gemini_payload = json.dumps(
        {
            "raw_hazard": "flood",
            "raw_severity": "Moderate",
            "raw_location": "Nirmala",
            "raw_start_time": "2025-07-17 00:00",
            "raw_end_time": None,
            "raw_action": "Move valuables to safety.",
        }
    )

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = gemini_payload
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        results = pipeline.process(incomplete_text, "plaintext")

    assert len(results) == 1
    alert = results[0]
    assert isinstance(alert, NormalizedAlert)
    assert alert.hazard_type == "other"
    assert alert.severity == "Moderate"
    assert alert.location_name == "Nirmala"


def test_e2e_mixed_format_processing() -> None:
    """Scenario 6: Verify mixed-format independent processing across all supported formats."""
    pipeline = AlertPipeline()

    with open("data/raw_alerts_json.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    with open("data/raw_alerts_cap.xml", "r", encoding="utf-8") as f:
        cap_data = f.read()
    with open("data/raw_alerts_rss.xml", "r", encoding="utf-8") as f:
        rss_data = f.read()
    with open("data/raw_alerts_plaintext.txt", "r", encoding="utf-8") as f:
        pt_data = f.read()

    json_res = pipeline.process(json_data, "json")
    cap_res = pipeline.process(cap_data, "cap_xml")
    rss_res = pipeline.process(rss_data, "rss")
    pt_res = pipeline.process(pt_data, "plaintext")

    assert len(json_res) > 0
    assert len(cap_res) > 0
    assert len(rss_res) > 0
    assert len(pt_res) > 0

    all_alerts = json_res + cap_res + rss_res + pt_res
    assert all(isinstance(alert, NormalizedAlert) for alert in all_alerts)


def test_e2e_empty_dataset_handling() -> None:
    """Scenario 7: Verify empty dataset handling returns [] gracefully."""
    pipeline = AlertPipeline()

    assert pipeline.process([], "json") == []
    assert pipeline.process("", "cap_xml") == []
    assert pipeline.process(None, "rss") == []
    assert pipeline.process("   ", "plaintext") == []


def test_e2e_unsupported_format_handling() -> None:
    """Scenario 8: Verify unsupported format handling raises descriptive ValueError."""
    pipeline = AlertPipeline()

    with pytest.raises(ValueError, match="Unsupported source format: 'yaml'"):
        pipeline.process([], "yaml")

    with pytest.raises(ValueError, match="Unsupported source format: 'csv'"):
        pipeline.process([], "csv")

    with pytest.raises(ValueError, match="Invalid source format"):
        pipeline.process([], "")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Invalid source format"):
        pipeline.process([], None)  # type: ignore[arg-type]


def test_e2e_duplicate_propagation() -> None:
    """Scenario 9: Verify duplicate flags propagate correctly across duplicate alerts in a batch."""
    pipeline = AlertPipeline()
    duplicate_json = [
        {
            "id": "DUP-001",
            "event": "Heat Wave",
            "area": "Devapur",
            "severity": "Red",
            "urgency": "Expected",
            "certainty": "Observed",
            "startTime": "2025-07-18 03:00",
            "expires": "2025-07-19 03:00",
            "recommended_action": "Stay indoors and drink water.",
            "source": "Source A",
        },
        {
            "id": "DUP-002",
            "event": "Heat Wave",
            "area": "Devapur",
            "severity": "Red",
            "urgency": "Expected",
            "certainty": "Observed",
            "startTime": "2025-07-18 03:00",
            "expires": "2025-07-19 03:00",
            "recommended_action": "Stay indoors and drink water.",
            "source": "Source B",
        },
    ]

    results = pipeline.process(duplicate_json, "json")

    assert len(results) == 2
    assert results[0].is_duplicate is False
    assert results[1].is_duplicate is True


def test_e2e_warning_propagation() -> None:
    """Scenario 10: Verify parse warnings propagate into final NormalizedAlert objects."""
    pipeline = AlertPipeline()
    data_with_unknowns = [
        {
            "id": "WARN-001",
            "event": "Custom Disaster Event",
            "area": "Unknown Location 99",
            "severity": "Unknown Level",
            "advice": "Take care.",
            "source": "Unknown Source",
        }
    ]

    results = pipeline.process(data_with_unknowns, "json")

    assert len(results) == 1
    alert = results[0]
    assert isinstance(alert, NormalizedAlert)
    assert len(alert.parse_warnings) > 0
    assert alert.location_id is None
    assert alert.severity == "Unknown"


def test_e2e_input_immutability() -> None:
    """Scenario 11: Verify pipeline never mutates input objects or lists."""
    pipeline = AlertPipeline()
    original_dict = {
        "id": "IMMUT-001",
        "event": "Urban Flood",
        "area": "Nirmala",
        "severity": "Moderate",
        "advice": "Move up.",
    }
    input_data = [dict(original_dict)]
    input_copy = [dict(original_dict)]

    _ = pipeline.process(input_data, "json")

    assert input_data == input_copy
    assert input_data[0] == original_dict


def test_e2e_batch_processing() -> None:
    """Scenario 12: Verify batch processing capability over multi-record inputs."""
    pipeline = AlertPipeline()
    with open("data/raw_alerts_json.json", "r", encoding="utf-8") as f:
        raw_json_data = json.load(f)

    results = pipeline.process(raw_json_data, "json")

    assert isinstance(results, list)
    assert len(results) == len(raw_json_data)
    assert all(isinstance(alert, NormalizedAlert) for alert in results)


def test_e2e_regression() -> None:
    """Scenario 13: Regression verification on all provided dataset files."""
    pipeline = AlertPipeline()

    with open("data/raw_alerts_json.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    with open("data/raw_alerts_cap.xml", "r", encoding="utf-8") as f:
        cap_data = f.read()
    with open("data/raw_alerts_rss.xml", "r", encoding="utf-8") as f:
        rss_data = f.read()
    with open("data/raw_alerts_plaintext.txt", "r", encoding="utf-8") as f:
        pt_data = f.read()

    for data, fmt in [
        (json_data, "json"),
        (cap_data, "cap_xml"),
        (rss_data, "rss"),
        (pt_data, "plaintext"),
    ]:
        res = pipeline.process(data, fmt)
        assert len(res) > 0
        for alert in res:
            assert isinstance(alert, NormalizedAlert)
            assert alert.alert_id != ""
            assert alert.hazard_type in [
                "flood",
                "heatwave",
                "cyclone",
                "landslide",
                "lightning",
                "earthquake",
                "other",
            ]
            assert alert.severity in ["Minor", "Moderate", "Severe", "Extreme", "Unknown"]
            assert alert.urgency in ["Immediate", "Expected", "Future", "Past", "Unknown"]
            assert alert.certainty in ["Observed", "Likely", "Possible", "Unknown"]


def test_e2e_output_contract() -> None:
    """Scenario 14: Verify pipeline output contract (List[NormalizedAlert], no invalid objects)."""
    pipeline = AlertPipeline()
    with open("data/raw_alerts_json.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)

    results = pipeline.process(json_data, "json")

    assert isinstance(results, list)
    for alert in results:
        assert isinstance(alert, NormalizedAlert)
        # Verify mandatory attributes from expected schema
        assert hasattr(alert, "alert_id")
        assert hasattr(alert, "source")
        assert hasattr(alert, "hazard_type")
        assert hasattr(alert, "severity")
        assert hasattr(alert, "urgency")
        assert hasattr(alert, "certainty")
        assert hasattr(alert, "location_name")
        assert hasattr(alert, "recommended_action")
        assert hasattr(alert, "source_format")
        assert hasattr(alert, "is_duplicate")
        assert hasattr(alert, "parse_warnings")


def test_e2e_system_stability_repeated_execution() -> None:
    """Scenario 15: Verify complete system stability under repeated execution."""
    pipeline = AlertPipeline()
    with open("data/raw_alerts_json.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    runs = [pipeline.process(raw_data, "json") for _ in range(5)]

    # Assert deterministic output counts
    assert all(len(r) == len(runs[0]) for r in runs)

    # Assert deterministic values across runs
    first_run_dumps = [alert.model_dump() for alert in runs[0]]
    for nth_run in runs[1:]:
        nth_run_dumps = [alert.model_dump() for alert in nth_run]
        assert nth_run_dumps == first_run_dumps
