"""Core Pydantic data models for Alert Intelligence Engine."""

from typing import Any, Dict, List, Literal, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ConfigDict, Field

# Enum Literals defining expected schema domain values
HazardType = Literal["flood", "heatwave", "cyclone", "landslide", "lightning", "earthquake", "other"]
SeverityType = Literal["Minor", "Moderate", "Severe", "Extreme", "Unknown"]
UrgencyType = Literal["Immediate", "Expected", "Future", "Past", "Unknown"]
CertaintyType = Literal["Observed", "Likely", "Possible", "Unknown"]
SourceFormatType = Literal["json", "cap_xml", "rss", "plaintext"]


class ParsedAlert(BaseModel):
    """Intermediate data model holding unnormalized extracted fields from raw input files."""

    model_config = ConfigDict(extra="forbid")

    raw_hazard: Optional[str] = None
    raw_severity: Optional[str] = None
    raw_urgency: Optional[str] = None
    raw_certainty: Optional[str] = None
    raw_location: Optional[str] = None
    raw_start_time: Optional[str] = None
    raw_end_time: Optional[str] = None
    raw_action: Optional[str] = None
    source: str
    source_format: SourceFormatType
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    parse_warnings: List[str] = Field(default_factory=list)


class NormalizedAlert(BaseModel):
    """Final normalized data model matching expected_normalized_schema.json."""

    model_config = ConfigDict(extra="forbid")

    alert_id: str
    source: str
    hazard_type: HazardType
    severity: SeverityType
    urgency: UrgencyType
    certainty: CertaintyType
    location_name: str
    location_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    recommended_action: str
    source_format: SourceFormatType
    is_duplicate: bool = False
    parse_warnings: List[str] = Field(default_factory=list)
