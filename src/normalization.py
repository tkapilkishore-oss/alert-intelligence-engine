"""Normalization Engine module for Alert Intelligence Engine."""

from typing import List, Optional
from src.logger import get_logger
from src.mappers.certainty_mapper import CertaintyMapper
from src.mappers.datetime_mapper import DatetimeMapper
from src.mappers.hazard_mapper import HazardMapper
from src.mappers.location_mapper import LocationMapper
from src.mappers.severity_mapper import SeverityMapper
from src.mappers.urgency_mapper import UrgencyMapper
from src.schema import NormalizedAlert, ParsedAlert

logger = get_logger(__name__)


class NormalizationEngine:
    """Core Normalization Engine converting intermediate ParsedAlert objects into schema-compliant NormalizedAlert objects."""

    def __init__(
        self,
        hazard_mapper: Optional[HazardMapper] = None,
        severity_mapper: Optional[SeverityMapper] = None,
        urgency_mapper: Optional[UrgencyMapper] = None,
        certainty_mapper: Optional[CertaintyMapper] = None,
        location_mapper: Optional[LocationMapper] = None,
        datetime_mapper: Optional[DatetimeMapper] = None,
    ) -> None:
        """Initialize NormalizationEngine with individual field mappers.

        Args:
            hazard_mapper: Optional HazardMapper instance override.
            severity_mapper: Optional SeverityMapper instance override.
            urgency_mapper: Optional UrgencyMapper instance override.
            certainty_mapper: Optional CertaintyMapper instance override.
            location_mapper: Optional LocationMapper instance override.
            datetime_mapper: Optional DatetimeMapper instance override.
        """
        self._hazard_mapper = hazard_mapper or HazardMapper()
        self._severity_mapper = severity_mapper or SeverityMapper()
        self._urgency_mapper = urgency_mapper or UrgencyMapper()
        self._certainty_mapper = certainty_mapper or CertaintyMapper()
        self._location_mapper = location_mapper or LocationMapper()
        self._datetime_mapper = datetime_mapper or DatetimeMapper()

    def normalize(self, alert: ParsedAlert) -> NormalizedAlert:
        """Normalize an intermediate ParsedAlert object into a new NormalizedAlert.

        Guarantees input immutability: incoming ParsedAlert is never mutated.

        Args:
            alert: Unnormalized incoming ParsedAlert.

        Returns:
            NormalizedAlert: Standardized, schema-compliant NormalizedAlert instance.
        """
        # Preserve original parse_warnings by creating a shallow copy list
        warnings: List[str] = list(alert.parse_warnings)

        # 1. Map Hazard Type
        hazard_type, hazard_warn = self._hazard_mapper.map_hazard(alert.raw_hazard)
        if hazard_warn:
            warnings.append(hazard_warn)

        # 2. Map Severity
        severity, severity_warn = self._severity_mapper.map_severity(alert.raw_severity)
        if severity_warn:
            warnings.append(severity_warn)

        # 3. Map Urgency
        urgency, urgency_warn = self._urgency_mapper.map_urgency(alert.raw_urgency)
        if urgency_warn:
            warnings.append(urgency_warn)

        # 4. Map Certainty
        certainty, certainty_warn = self._certainty_mapper.map_certainty(alert.raw_certainty)
        if certainty_warn:
            warnings.append(certainty_warn)

        # 5. Map Location
        location_name, location_id, loc_warn = self._location_mapper.map_location(alert.raw_location)
        if loc_warn:
            warnings.append(loc_warn)

        # 6. Map Datetimes
        start_time, start_warn = self._datetime_mapper.map_datetime(alert.raw_start_time)
        if start_warn:
            warnings.append(start_warn)

        end_time, end_warn = self._datetime_mapper.map_datetime(alert.raw_end_time)
        if end_warn:
            warnings.append(end_warn)

        # 7. Extract alert_id from raw_payload or fallback
        alert_id = self._extract_alert_id(alert)

        # 8. Extract recommended_action or fallback
        recommended_action = alert.raw_action.strip() if alert.raw_action and alert.raw_action.strip() else "No action specified"

        return NormalizedAlert(
            alert_id=alert_id,
            source=alert.source,
            hazard_type=hazard_type,
            severity=severity,
            urgency=urgency,
            certainty=certainty,
            location_name=location_name,
            location_id=location_id,
            start_time=start_time,
            end_time=end_time,
            recommended_action=recommended_action,
            source_format=alert.source_format,
            is_duplicate=False,
            parse_warnings=warnings,
        )

    def _extract_alert_id(self, alert: ParsedAlert) -> str:
        """Extract explicit alert identifier from raw_payload dictionary or construct fallback ID."""
        payload = alert.raw_payload or {}
        for key in ("alert_id", "id", "identifier", "guid", "alertCode"):
            if key in payload and payload[key]:
                return str(payload[key]).strip()

        return f"{alert.source_format.upper()}-UNKNOWN"
