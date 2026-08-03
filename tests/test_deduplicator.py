"""Unit tests for Stage 9 Deduplication Engine."""

from src.deduplicator import DeduplicationEngine
from src.schema import NormalizedAlert


def _create_sample_alert(
    alert_id: str = "JSON-001",
    source: str = "Demo IMD Feed",
    hazard_type: str = "flood",
    severity: str = "Moderate",
    urgency: str = "Future",
    certainty: str = "Likely",
    location_name: str = "Nirmala",
    location_id: str = "DIST-001",
    start_time: str = "2025-07-17T03:00:00",
    end_time: str = "2025-07-18T15:00:00",
    recommended_action: str = "Avoid low-lying roads and move valuables above ground level.",
    source_format: str = "json",
    is_duplicate: bool = False,
) -> NormalizedAlert:
    return NormalizedAlert(
        alert_id=alert_id,
        source=source,
        hazard_type=hazard_type,
        severity=severity,
        urgency=urgency,
        certainty=certainty,
        location_name=location_name,
        location_id=location_id,
        start_time=start_time,
        end_time=end_time,
        recommended_action=recommended_action,
        source_format=source_format,
        is_duplicate=is_duplicate,
        parse_warnings=[],
    )


# 1. Duplicate alerts
def test_duplicate_alerts():
    engine = DeduplicationEngine()
    alert1 = _create_sample_alert(alert_id="JSON-001")
    alert2 = _create_sample_alert(alert_id="JSON-002", source="District Control Room")

    result = engine.deduplicate([alert1, alert2])

    assert len(result) == 2
    assert result[0].is_duplicate is False
    assert result[1].is_duplicate is True


# 2. Non-duplicate alerts
def test_non_duplicate_alerts():
    engine = DeduplicationEngine()
    alert1 = _create_sample_alert(alert_id="JSON-001", hazard_type="flood", location_id="DIST-001")
    alert2 = _create_sample_alert(alert_id="JSON-002", hazard_type="earthquake", location_id="DIST-002")

    result = engine.deduplicate([alert1, alert2])

    assert len(result) == 2
    assert result[0].is_duplicate is False
    assert result[1].is_duplicate is False


# 3. Borderline threshold behavior
def test_borderline_threshold_behavior():
    engine = DeduplicationEngine()
    alert_ref = _create_sample_alert(alert_id="REF-001")

    # Score calculation:
    # Hazard match (0.35) + Location match (0.30) + Time match (0.20) + Action match (0.15) = 1.0
    # Let's test score == 0.75
    # If Hazard matches (0.35), Location matches (0.30), Action matches (0.15), Time = 0.0 -> Score = 0.80 >= 0.75 -> True
    # If Hazard matches (0.35), Time matches (0.20), Action matches (0.15), Location differs (0.0) -> Score = 0.70 < 0.75 -> False

    # Score exactly 0.80 >= 0.75
    alert_above = alert_ref.model_copy(update={"alert_id": "ABOVE-001", "start_time": "2026-01-01T00:00:00"})
    res_above = engine.deduplicate([alert_ref, alert_above])
    assert res_above[1].is_duplicate is True

    # Score exactly 0.70 < 0.75
    alert_below = alert_ref.model_copy(update={"alert_id": "BELOW-001", "location_id": "DIST-999", "location_name": "Somewhere Else"})
    res_below = engine.deduplicate([alert_ref, alert_below])
    assert res_below[1].is_duplicate is False


# 4. Empty list
def test_empty_list():
    engine = DeduplicationEngine()
    assert engine.deduplicate([]) == []


# 5. Single alert
def test_single_alert():
    engine = DeduplicationEngine()
    alert = _create_sample_alert(alert_id="SINGLE-001")
    result = engine.deduplicate([alert])

    assert len(result) == 1
    assert result[0].is_duplicate is False


# 6. Different hazard
def test_different_hazard():
    engine = DeduplicationEngine()
    alert1 = _create_sample_alert(hazard_type="flood")
    alert2 = _create_sample_alert(hazard_type="heatwave")

    # Hazard differs: max possible score without hazard match is 0.65 < 0.75
    result = engine.deduplicate([alert1, alert2])

    assert result[0].is_duplicate is False
    assert result[1].is_duplicate is False


# 7. Different location
def test_different_location():
    engine = DeduplicationEngine()
    alert1 = _create_sample_alert(location_id="DIST-001", location_name="District 1")
    alert2 = _create_sample_alert(location_id="DIST-002", location_name="District 2")

    # Priority 1: both location_id present and different -> location score = 0.0
    # Max possible score without location match is 0.70 < 0.75
    result = engine.deduplicate([alert1, alert2])

    assert result[0].is_duplicate is False
    assert result[1].is_duplicate is False


# 8. Different time windows
def test_different_time_windows():
    engine = DeduplicationEngine()
    # Non-overlapping time windows: July 2025 vs August 2025
    alert1 = _create_sample_alert(start_time="2025-07-01T00:00:00", end_time="2025-07-02T00:00:00")
    alert2 = _create_sample_alert(start_time="2025-08-01T00:00:00", end_time="2025-08-02T00:00:00")

    # Time overlap score = 0.0
    # Score = 0.35 (hazard) + 0.30 (location) + 0.00 (time) + 0.15 (action) = 0.80 >= 0.75 -> True
    # If action also differs: 0.35 + 0.30 + 0.0 + 0.0 = 0.65 < 0.75 -> False
    alert2_diff_action = alert2.model_copy(update={"recommended_action": "Completely different action instruction."})
    result = engine.deduplicate([alert1, alert2_diff_action])

    assert result[0].is_duplicate is False
    assert result[1].is_duplicate is False


# 9. Different recommended actions
def test_different_recommended_actions():
    engine = DeduplicationEngine()
    alert1 = _create_sample_alert(recommended_action="Move to high ground immediately.")
    alert2 = _create_sample_alert(recommended_action="Stay indoors away from windows.")

    score = engine._text_similarity_score(alert1, alert2)
    assert score < 0.5


# 10. Large batch handling
def test_large_batch_handling():
    engine = DeduplicationEngine()
    batch = []
    # 100 alerts: 50 unique events, each duplicated once
    for i in range(50):
        a1 = _create_sample_alert(alert_id=f"ALERT-{i:03d}-A", location_id=f"LOC-{i:03d}")
        a2 = _create_sample_alert(alert_id=f"ALERT-{i:03d}-B", location_id=f"LOC-{i:03d}")
        batch.extend([a1, a2])

    result = engine.deduplicate(batch)

    assert len(result) == 100
    duplicates = [a for a in result if a.is_duplicate]
    canonical = [a for a in result if not a.is_duplicate]
    assert len(duplicates) == 50
    assert len(canonical) == 50


# 11. Input immutability
def test_input_immutability():
    engine = DeduplicationEngine()
    alert1 = _create_sample_alert(alert_id="JSON-001", is_duplicate=False)
    alert2 = _create_sample_alert(alert_id="JSON-002", is_duplicate=False)

    input_list = [alert1, alert2]
    original_input_list = list(input_list)

    result = engine.deduplicate(input_list)

    assert input_list == original_input_list
    assert alert1.is_duplicate is False
    assert alert2.is_duplicate is False  # Original object not mutated!
    assert result[1].is_duplicate is True  # Returned object has updated flag


# 12. Existing alerts remain unchanged except duplicate flag in returned results
def test_existing_alerts_field_preservation():
    engine = DeduplicationEngine()
    alert1 = _create_sample_alert(alert_id="JSON-001")
    alert2 = _create_sample_alert(alert_id="JSON-002")

    result = engine.deduplicate([alert1, alert2])

    dup_alert = result[1]
    assert dup_alert.alert_id == alert2.alert_id
    assert dup_alert.source == alert2.source
    assert dup_alert.hazard_type == alert2.hazard_type
    assert dup_alert.severity == alert2.severity
    assert dup_alert.urgency == alert2.urgency
    assert dup_alert.certainty == alert2.certainty
    assert dup_alert.location_name == alert2.location_name
    assert dup_alert.location_id == alert2.location_id
    assert dup_alert.start_time == alert2.start_time
    assert dup_alert.end_time == alert2.end_time
    assert dup_alert.recommended_action == alert2.recommended_action
    assert dup_alert.source_format == alert2.source_format
    assert dup_alert.parse_warnings == alert2.parse_warnings
    assert dup_alert.is_duplicate is True
