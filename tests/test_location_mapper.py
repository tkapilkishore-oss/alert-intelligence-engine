"""Unit tests for LocationMapper."""

import pytest
from src.mappers.location_mapper import LocationMapper


def test_location_mapper_valid_reference_lookup() -> None:
    mapper = LocationMapper()

    # District lookups
    loc_name, loc_id, warning = mapper.map_location("Nirmala")
    assert loc_name == "Nirmala"
    assert loc_id == "DIST-01"
    assert warning is None

    loc_name, loc_id, warning = mapper.map_location("Suryanagar")
    assert loc_name == "Suryanagar"
    assert loc_id == "DIST-02"
    assert warning is None

    # Block lookups
    loc_name, loc_id, warning = mapper.map_location("Devapur Block 2")
    assert loc_name == "Devapur Block 2"
    assert loc_id == "BLK-03-2"
    assert warning is None


def test_location_mapper_unknown_location() -> None:
    mapper = LocationMapper()
    loc_name, loc_id, warning = mapper.map_location("Atlantis City")
    assert loc_name == "Atlantis City"
    assert loc_id is None
    assert warning is not None
    assert "Unknown location: 'Atlantis City'" in warning


def test_location_mapper_missing_location() -> None:
    mapper = LocationMapper()
    loc_name, loc_id, warning = mapper.map_location(None)
    assert loc_name == "Unknown Location"
    assert loc_id is None
    assert warning is not None
    assert "Missing raw location" in warning
