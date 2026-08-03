"""Unit tests for SeverityMapper."""

import pytest
from src.mappers.severity_mapper import SeverityMapper


def test_severity_mapper_reference_csv_lookup() -> None:
    mapper = SeverityMapper()

    # Extreme mappings
    assert mapper.map_severity("Red")[0] == "Extreme"
    assert mapper.map_severity("RED ALERT")[0] == "Extreme"
    assert mapper.map_severity("Extreme")[0] == "Extreme"

    # Severe mappings
    assert mapper.map_severity("Severe")[0] == "Severe"
    assert mapper.map_severity("Orange")[0] == "Severe"
    assert mapper.map_severity("High")[0] == "Severe"

    # Moderate mappings
    assert mapper.map_severity("Moderate")[0] == "Moderate"
    assert mapper.map_severity("Yellow")[0] == "Moderate"

    # Minor mappings
    assert mapper.map_severity("Watch")[0] == "Minor"
    assert mapper.map_severity("Advisory")[0] == "Minor"
    assert mapper.map_severity("Low")[0] == "Minor"


def test_severity_mapper_unknown_term() -> None:
    mapper = SeverityMapper()
    sev, warning = mapper.map_severity("Catastrophic")
    assert sev == "Unknown"
    assert warning is not None
    assert "Unknown severity term" in warning


def test_severity_mapper_missing_term() -> None:
    mapper = SeverityMapper()
    sev, warning = mapper.map_severity(None)
    assert sev == "Unknown"
    assert warning is not None
    assert "Missing raw severity" in warning
