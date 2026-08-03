"""Validation Engine module for Stage 8 Alert Intelligence Engine."""

from datetime import datetime
from typing import Any, List
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.logger import get_logger
from src.schema import NormalizedAlert, ParsedAlert

logger = get_logger(__name__)

VALID_SOURCE_FORMATS = {"json", "cap_xml", "rss", "plaintext"}


class ValidationResult(BaseModel):
    """Structured result model returned by ValidationEngine validation checks."""

    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ValidationEngine:
    """Engine responsible for structural validation of ParsedAlert and schema validation of NormalizedAlert."""

    def validate_structure(self, alert: Any) -> ValidationResult:
        """Perform structural validation on an intermediate ParsedAlert object.

        Inspects parser output immediately after parsing to determine if minimum
        required information exists to continue processing through the pipeline.

        Guarantees input immutability: incoming ParsedAlert is never mutated.

        Args:
            alert: Unnormalized incoming ParsedAlert object (or raw input).

        Returns:
            ValidationResult: Structured result indicating structural usability,
                errors, and validation warnings.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(alert, ParsedAlert):
            msg = f"Input is not a valid ParsedAlert instance: got {type(alert).__name__}"
            logger.warning(msg)
            return ValidationResult(is_valid=False, errors=[msg], warnings=[])

        # 1. Source Check
        if not alert.source or not str(alert.source).strip():
            errors.append("Missing or empty alert source")

        # 2. Source Format Check
        if not alert.source_format or str(alert.source_format).strip() not in VALID_SOURCE_FORMATS:
            errors.append(f"Missing or invalid source_format: '{alert.source_format}'")

        # 3. Payload Type Check
        if alert.raw_payload is None or not isinstance(alert.raw_payload, dict):
            errors.append("raw_payload must be a valid dictionary")

        # 4. Check for empty parser output / usable content
        raw_fields = [
            alert.raw_hazard,
            alert.raw_severity,
            alert.raw_urgency,
            alert.raw_certainty,
            alert.raw_location,
            alert.raw_start_time,
            alert.raw_end_time,
            alert.raw_action,
        ]
        has_raw_field = any(f is not None and str(f).strip() != "" for f in raw_fields)
        has_payload = bool(alert.raw_payload)

        if not has_raw_field and not has_payload:
            errors.append("Empty parser output: no raw fields or payload content present")

        # 5. Preserve existing parse warnings without mutating incoming object
        warnings.extend(alert.parse_warnings)

        # 6. Collect validation warnings for missing optional raw fields
        self._collect_structural_warnings(alert, warnings)

        is_valid = len(errors) == 0
        if not is_valid:
            logger.info(f"Structural validation failed with errors: {errors}")

        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    def validate_schema(self, alert: Any) -> ValidationResult:
        """Perform schema validation on a NormalizedAlert object.

        Validates the object against the final expected schema constraints,
        checking required fields, enums, data types, ISO-8601 datetimes, and
        parse warning structure.

        Guarantees input immutability: incoming NormalizedAlert is never mutated.

        Args:
            alert: NormalizedAlert object after normalization.

        Returns:
            ValidationResult: Structured result indicating schema compliance,
                errors, and validation warnings.
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(alert, NormalizedAlert):
            # Attempt dict validation if dict is passed
            if isinstance(alert, dict):
                try:
                    norm_obj = NormalizedAlert.model_validate(alert)
                    return self.validate_schema(norm_obj)
                except ValidationError as ve:
                    for err in ve.errors():
                        loc = ".".join(str(x) for x in err["loc"])
                        errors.append(f"Field '{loc}': {err['msg']}")
                    return ValidationResult(is_valid=False, errors=errors, warnings=[])
            else:
                msg = f"Input is not a valid NormalizedAlert instance: got {type(alert).__name__}"
                logger.warning(msg)
                return ValidationResult(is_valid=False, errors=[msg], warnings=[])

        # 1. Pydantic Model Validation (Catches Enum and Required Field violations if mutated or dict-constructed)
        try:
            alert_dict = {k: getattr(alert, k) for k in type(alert).model_fields} if hasattr(type(alert), "model_fields") else alert.model_dump()
            NormalizedAlert.model_validate(alert_dict)
        except ValidationError as ve:
            for err in ve.errors():
                loc = ".".join(str(x) for x in err["loc"])
                errors.append(f"Field '{loc}': {err['msg']}")

        # 2. Strict Field Datatype and Contract Checks
        self._check_schema_types_and_contracts(alert, errors)

        # 3. Preserve parse warnings
        if isinstance(alert.parse_warnings, list):
            warnings.extend([w for w in alert.parse_warnings if isinstance(w, str)])

        is_valid = len(errors) == 0
        if not is_valid:
            logger.info(f"Schema validation failed with errors: {errors}")

        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    def _collect_structural_warnings(self, alert: ParsedAlert, warnings: List[str]) -> None:
        """Private helper to inspect optional raw fields and collect structural warnings."""
        if not alert.raw_hazard or not str(alert.raw_hazard).strip():
            warnings.append("Missing raw hazard")
        if not alert.raw_severity or not str(alert.raw_severity).strip():
            warnings.append("Missing raw severity")
        if not alert.raw_location or not str(alert.raw_location).strip():
            warnings.append("Missing raw location")
        if not alert.raw_start_time or not str(alert.raw_start_time).strip():
            warnings.append("Missing raw start_time")
        if not alert.raw_end_time or not str(alert.raw_end_time).strip():
            warnings.append("Missing raw end_time")
        if not alert.raw_action or not str(alert.raw_action).strip():
            warnings.append("Missing raw action")
        if not alert.raw_payload:
            warnings.append("raw_payload is empty")

    def _check_schema_types_and_contracts(self, alert: NormalizedAlert, errors: List[str]) -> None:
        """Private helper to verify strict field types, ISO datetimes, and schema contracts."""
        # Non-empty string checks for mandatory text fields
        if not alert.alert_id or not str(alert.alert_id).strip():
            errors.append("Field 'alert_id' cannot be empty")
        if not alert.source or not str(alert.source).strip():
            errors.append("Field 'source' cannot be empty")
        if not alert.location_name or not str(alert.location_name).strip():
            errors.append("Field 'location_name' cannot be empty")
        if not alert.recommended_action or not str(alert.recommended_action).strip():
            errors.append("Field 'recommended_action' cannot be empty")

        # Duplicate flag type check
        if type(alert.is_duplicate) is not bool:
            errors.append(f"Field 'is_duplicate' must be a boolean, got {type(alert.is_duplicate).__name__}")

        # Location ID type check
        if alert.location_id is not None and not isinstance(alert.location_id, str):
            errors.append(f"Field 'location_id' must be a string or None, got {type(alert.location_id).__name__}")

        # Parse warnings list and element type check
        if not isinstance(alert.parse_warnings, list):
            errors.append(f"Field 'parse_warnings' must be a list, got {type(alert.parse_warnings).__name__}")
        else:
            if any(not isinstance(w, str) for w in alert.parse_warnings):
                errors.append("Field 'parse_warnings' list must contain only strings")

        # Datetime ISO-8601 checks
        if alert.start_time is not None:
            if not isinstance(alert.start_time, str):
                errors.append(f"Field 'start_time' must be an ISO-8601 string or None, got {type(alert.start_time).__name__}")
            else:
                try:
                    datetime.fromisoformat(alert.start_time)
                except (ValueError, TypeError):
                    errors.append(f"Field 'start_time' is not a valid ISO-8601 datetime: '{alert.start_time}'")

        if alert.end_time is not None:
            if not isinstance(alert.end_time, str):
                errors.append(f"Field 'end_time' must be an ISO-8601 string or None, got {type(alert.end_time).__name__}")
            else:
                try:
                    datetime.fromisoformat(alert.end_time)
                except (ValueError, TypeError):
                    errors.append(f"Field 'end_time' is not a valid ISO-8601 datetime: '{alert.end_time}'")
