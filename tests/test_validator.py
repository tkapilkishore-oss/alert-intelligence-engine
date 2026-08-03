"""Unit tests for ValidationEngine module (Stage 8)."""

import pytest
from src.schema import NormalizedAlert, ParsedAlert
from src.validator import ValidationEngine, ValidationResult


@pytest.fixture
def validator() -> ValidationEngine:
    """Fixture providing ValidationEngine instance."""
    return ValidationEngine()


@pytest.fixture
def sample_valid_parsed_alert() -> ParsedAlert:
    """Fixture providing a fully valid ParsedAlert object."""
    return ParsedAlert(
        raw_hazard="flood",
        raw_severity="Moderate",
        raw_urgency="Future",
        raw_certainty="Likely",
        raw_location="Nirmala",
        raw_start_time="2025-07-17T03:00:00",
        raw_end_time="2025-07-18T15:00:00",
        raw_action="Evacuate",
        source="Demo Feed",
        source_format="json",
        raw_payload={"alert_id": "JSON-001"},
        parse_warnings=[],
    )


@pytest.fixture
def sample_valid_normalized_alert() -> NormalizedAlert:
    """Fixture providing a fully valid NormalizedAlert object."""
    return NormalizedAlert(
        alert_id="JSON-001",
        source="Demo Feed",
        hazard_type="flood",
        severity="Moderate",
        urgency="Future",
        certainty="Likely",
        location_name="Nirmala",
        location_id="DIST-01",
        start_time="2025-07-17T03:00:00",
        end_time="2025-07-18T15:00:00",
        recommended_action="Avoid low-lying roads.",
        source_format="json",
        is_duplicate=False,
        parse_warnings=[],
    )


# 1. Structural Validation — Valid ParsedAlert
def test_valid_parsed_alert(validator: ValidationEngine, sample_valid_parsed_alert: ParsedAlert) -> None:
    """Verify structural validation passes for a valid ParsedAlert."""
    res = validator.validate_structure(sample_valid_parsed_alert)
    assert isinstance(res, ValidationResult)
    assert res.is_valid is True
    assert res.errors == []


# 2. Structural Validation — Invalid ParsedAlert (Not a ParsedAlert object)
def test_invalid_parsed_alert(validator: ValidationEngine) -> None:
    """Verify structural validation rejects non-ParsedAlert inputs (strings, dicts, None, ints)."""
    assert validator.validate_structure(None).is_valid is False
    assert validator.validate_structure("invalid alert string").is_valid is False
    assert validator.validate_structure(12345).is_valid is False
    assert validator.validate_structure({"source": "demo"}).is_valid is False

    res = validator.validate_structure(None)
    assert any("Input is not a valid ParsedAlert instance" in err for err in res.errors)


# 3. Structural Validation — Missing Payload
def test_missing_payload(validator: ValidationEngine) -> None:
    """Verify structural validation handles missing/empty raw_payload dictionary."""
    alert = ParsedAlert(
        raw_hazard="flood",
        source="demo",
        source_format="json",
        raw_payload={},
    )
    res = validator.validate_structure(alert)
    assert res.is_valid is True
    assert "raw_payload is empty" in res.warnings


# 4. Structural Validation — Missing Source
def test_missing_source(validator: ValidationEngine) -> None:
    """Verify structural validation rejects ParsedAlert with empty or missing source."""
    alert_empty_source = ParsedAlert(
        raw_hazard="flood",
        source="",
        source_format="json",
        raw_payload={"data": "test"},
    )
    res = validator.validate_structure(alert_empty_source)
    assert res.is_valid is False
    assert "Missing or empty alert source" in res.errors


# 5. Structural Validation — Empty Parser Output
def test_empty_parser_output(validator: ValidationEngine) -> None:
    """Verify structural validation rejects empty parser output with no raw fields or payload."""
    alert_empty = ParsedAlert(
        source="demo",
        source_format="json",
        raw_payload={},
    )
    res = validator.validate_structure(alert_empty)
    assert res.is_valid is False
    assert any("Empty parser output" in err for err in res.errors)


# 6. Schema Validation — Valid NormalizedAlert
def test_valid_normalized_alert(validator: ValidationEngine, sample_valid_normalized_alert: NormalizedAlert) -> None:
    """Verify schema validation passes for a valid NormalizedAlert."""
    res = validator.validate_schema(sample_valid_normalized_alert)
    assert isinstance(res, ValidationResult)
    assert res.is_valid is True
    assert res.errors == []


# 7. Schema Validation — Invalid Enum
def test_invalid_enum(validator: ValidationEngine, sample_valid_normalized_alert: NormalizedAlert) -> None:
    """Verify schema validation detects invalid enum values."""
    data = sample_valid_normalized_alert.model_dump()
    data["severity"] = "SUPER RED"
    res = validator.validate_schema(data)
    assert res.is_valid is False
    assert len(res.errors) > 0


# 8. Schema Validation — Invalid Datatype
def test_invalid_datatype(validator: ValidationEngine, sample_valid_normalized_alert: NormalizedAlert) -> None:
    """Verify schema validation detects invalid datatypes (e.g. non-boolean is_duplicate or invalid datetime)."""
    # 8a. Invalid is_duplicate datatype
    alert = sample_valid_normalized_alert.model_copy(deep=True)
    object.__setattr__(alert, "is_duplicate", "yes")
    res1 = validator.validate_schema(alert)
    assert res1.is_valid is False
    assert any("is_duplicate" in err for err in res1.errors)

    # 8b. Invalid start_time datetime string
    alert2 = sample_valid_normalized_alert.model_copy(deep=True)
    alert2.start_time = "tomorrow morning"
    res2 = validator.validate_schema(alert2)
    assert res2.is_valid is False
    assert any("start_time" in err for err in res2.errors)


# 9. Schema Validation — Missing Required Fields
def test_missing_required_fields(validator: ValidationEngine, sample_valid_normalized_alert: NormalizedAlert) -> None:
    """Verify schema validation fails if mandatory fields are missing or empty."""
    data = sample_valid_normalized_alert.model_dump()
    del data["alert_id"]
    res = validator.validate_schema(data)
    assert res.is_valid is False
    assert len(res.errors) > 0

    alert_empty_id = sample_valid_normalized_alert.model_copy(deep=True)
    alert_empty_id.alert_id = ""
    res_empty = validator.validate_schema(alert_empty_id)
    assert res_empty.is_valid is False
    assert any("alert_id" in err for err in res_empty.errors)


# 10. Schema Validation — Malformed parse_warnings
def test_malformed_parse_warnings(validator: ValidationEngine, sample_valid_normalized_alert: NormalizedAlert) -> None:
    """Verify schema validation detects malformed parse_warnings field (e.g., non-list or list of integers)."""
    # Non-list parse_warnings
    alert = sample_valid_normalized_alert.model_copy(deep=True)
    object.__setattr__(alert, "parse_warnings", "warning string")
    res1 = validator.validate_schema(alert)
    assert res1.is_valid is False
    assert any("parse_warnings" in err for err in res1.errors)

    # List with non-string elements
    alert2 = sample_valid_normalized_alert.model_copy(deep=True)
    object.__setattr__(alert2, "parse_warnings", [123, 456])
    res2 = validator.validate_schema(alert2)
    assert res2.is_valid is False
    assert any("parse_warnings" in err for err in res2.errors)


# 11. Validation Warning Generation
def test_validation_warning_generation(validator: ValidationEngine) -> None:
    """Verify validation warnings are collected properly during structural validation."""
    alert = ParsedAlert(
        raw_hazard="flood",
        source="demo",
        source_format="json",
        raw_payload={"data": "sample"},
        parse_warnings=["Original parser warning"],
    )
    res = validator.validate_structure(alert)
    assert res.is_valid is True
    assert "Original parser warning" in res.warnings
    assert "Missing raw severity" in res.warnings
    assert "Missing raw location" in res.warnings


# 12. Input Immutability
def test_input_immutability(
    validator: ValidationEngine,
    sample_valid_parsed_alert: ParsedAlert,
    sample_valid_normalized_alert: NormalizedAlert,
) -> None:
    """Verify structural and schema validation never mutate input objects."""
    parsed_before = sample_valid_parsed_alert.model_dump()
    validator.validate_structure(sample_valid_parsed_alert)
    parsed_after = sample_valid_parsed_alert.model_dump()
    assert parsed_before == parsed_after

    normalized_before = sample_valid_normalized_alert.model_dump()
    validator.validate_schema(sample_valid_normalized_alert)
    normalized_after = sample_valid_normalized_alert.model_dump()
    assert normalized_before == normalized_after
