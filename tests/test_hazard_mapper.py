"""Unit tests for HazardMapper."""

# pyrefly: ignore [missing-import]
import pytest
from src.mappers.hazard_mapper import HazardMapper


def test_hazard_mapper_known_hazards() -> None:
    mapper = HazardMapper()
    assert mapper.map_hazard("Urban Flood")[0] == "flood"
    assert mapper.map_hazard("flood warning")[0] == "flood"
    assert mapper.map_hazard("Heat Wave")[0] == "heatwave"
    assert mapper.map_hazard("Cyclone Wind")[0] == "cyclone"
    assert mapper.map_hazard("landslide watch")[0] == "landslide"
    assert mapper.map_hazard("Lightning strike")[0] == "lightning"
    assert mapper.map_hazard("Earthquake tremor")[0] == "earthquake"


def test_hazard_mapper_unrecognized_hazard() -> None:
    mapper = HazardMapper()
    hazard, warning = mapper.map_hazard("alien invasion")
    assert hazard == "other"
    assert warning is not None
    assert "Unrecognized hazard term" in warning


def test_hazard_mapper_missing_hazard() -> None:
    mapper = HazardMapper()
    hazard, warning = mapper.map_hazard(None)
    assert hazard == "other"
    assert warning is not None
    assert "Missing raw hazard" in warning
