"""Plaintext Alert Parser module for Alert Intelligence Engine."""

import re
from typing import Any, Dict, List, Optional

from src.logger import get_logger
from src.parsers.base_parser import BaseParser
from src.schema import ParsedAlert

logger = get_logger(__name__)


class PlaintextParser(BaseParser):
    """Parser for unstructured plain text disaster alerts."""

    KNOWN_SEVERITIES = [
        "RED ALERT",
        "RED",
        "ORANGE",
        "YELLOW",
        "HIGH",
        "SEVERE",
        "MODERATE",
        "ADVISORY",
        "WATCH",
        "LOW",
    ]

    KNOWN_HAZARDS = [
        "flood warning",
        "urban flood",
        "flood",
        "heatwave",
        "heat stress",
        "cyclone wind",
        "cyclone",
        "landslide",
        "lightning",
        "heavy rain",
        "earthquake",
    ]

    def parse(self, raw_data: Any) -> List[ParsedAlert]:
        """Parse raw plain text alert data into a list of ParsedAlert intermediate objects.

        Args:
            raw_data: Raw input data (str, bytes, or List[str]).

        Returns:
            List[ParsedAlert]: List of extracted unnormalized ParsedAlert records.
        """
        lines = self._normalize_input(raw_data)
        parsed_alerts: List[ParsedAlert] = []

        for index, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue

            try:
                alert = self._parse_line(line_str)
                parsed_alerts.append(alert)
            except Exception as e:
                logger.warning(f"Failed to parse plaintext record at index {index}: {e}")

        return parsed_alerts

    def _normalize_input(self, raw_data: Any) -> List[str]:
        """Normalize raw input into a list of line strings."""
        if isinstance(raw_data, bytes):
            text = raw_data.decode("utf-8", errors="replace")
            return [line for line in text.splitlines() if line.strip()]
        elif isinstance(raw_data, str):
            return [line for line in raw_data.splitlines() if line.strip()]
        elif isinstance(raw_data, list):
            lines = []
            for item in raw_data:
                if isinstance(item, str):
                    lines.extend([l for l in item.splitlines() if l.strip()])
                elif isinstance(item, bytes):
                    decoded = item.decode("utf-8", errors="replace")
                    lines.extend([l for l in decoded.splitlines() if l.strip()])
                else:
                    logger.warning(f"Skipping non-string item in input list: {type(item).__name__}")
            return lines
        else:
            logger.warning(f"Unsupported input type for PlaintextParser: {type(raw_data).__name__}")
            return []

    def _detect_pattern(self, line: str) -> str:
        """Detect layout pattern of the given text line.

        Returns:
            str: One of 'pipe', 'colon', 'dash', or 'free_text'.
        """
        if "|" in line:
            return "pipe"
        elif ":" in line:
            return "colon"
        elif "-" in line:
            return "dash"
        else:
            return "free_text"

    def _parse_line(self, line: str) -> ParsedAlert:
        """Dispatch pattern detection and return constructed ParsedAlert."""
        pattern = self._detect_pattern(line)

        if pattern == "pipe":
            fields = self._parse_pipe_delimited(line)
        elif pattern == "colon":
            fields = self._parse_colon_format(line)
        elif pattern == "dash":
            fields = self._parse_dash_format(line)
        else:
            fields = self._parse_free_text(line)

        raw_hazard = fields.get("raw_hazard")
        raw_severity = fields.get("raw_severity")
        raw_urgency = fields.get("raw_urgency")
        raw_certainty = fields.get("raw_certainty")
        raw_location = fields.get("raw_location")
        raw_start_time = fields.get("raw_start_time")
        raw_end_time = fields.get("raw_end_time")
        raw_action = fields.get("raw_action")
        source = fields.get("source") or "Plaintext Alert System"

        parse_warnings: List[str] = list(fields.get("warnings", []))

        if not raw_hazard:
            parse_warnings.append("unable to extract hazard")
        if not raw_severity:
            parse_warnings.append("missing severity")
        if not raw_location:
            parse_warnings.append("missing location")
        if not raw_start_time:
            parse_warnings.append("missing start_time")

        raw_payload: Dict[str, Any] = {
            "original_text": line,
            "detected_pattern": pattern,
        }
        if "extra_payload" in fields and isinstance(fields["extra_payload"], dict):
            raw_payload.update(fields["extra_payload"])

        return ParsedAlert(
            raw_hazard=raw_hazard,
            raw_severity=raw_severity,
            raw_urgency=raw_urgency,
            raw_certainty=raw_certainty,
            raw_location=raw_location,
            raw_start_time=raw_start_time,
            raw_end_time=raw_end_time,
            raw_action=raw_action,
            source=source,
            source_format="plaintext",
            raw_payload=raw_payload,
            parse_warnings=parse_warnings,
        )

    def _parse_pipe_delimited(self, line: str) -> Dict[str, Any]:
        """Parse pipe-delimited alert lines (e.g. ALERT PT-001 | Devapur | Severe flood warning | ...)."""
        parts = [p.strip() for p in line.split("|")]
        res: Dict[str, Any] = {"warnings": []}

        if len(parts) >= 1:
            res["source"] = parts[0]
        if len(parts) >= 2:
            res["raw_location"] = parts[1]
        if len(parts) >= 3:
            sev, haz = self._extract_severity_and_hazard(parts[2])
            res["raw_severity"] = sev
            res["raw_hazard"] = haz
        if len(parts) >= 4:
            part4 = parts[3]
            sev_match = self._extract_known_severity(part4)
            if sev_match:
                res["raw_severity"] = sev_match
            elif re.search(r"starts|\d{4}-\d{2}-\d{2}", part4, re.IGNORECASE):
                res["raw_start_time"] = part4
            else:
                res["raw_action"] = part4
        if len(parts) >= 5:
            res["raw_action"] = parts[4]

        return res

    def _parse_colon_format(self, line: str) -> Dict[str, Any]:
        """Parse colon-delimited alert lines (e.g. PT-002 Suryanagar Block 2: HEATWAVE ORANGE...)."""
        res: Dict[str, Any] = {"warnings": []}
        header, body = [p.strip() for p in line.split(":", 1)]

        res["source"] = header
        location = self._extract_location_from_text(header)
        if location:
            res["raw_location"] = location

        body_loc = self._extract_location_after_for(body)
        if body_loc:
            res["raw_location"] = body_loc

        sev = self._extract_known_severity(body)
        if sev:
            res["raw_severity"] = sev

        haz = self._extract_known_hazard(body)
        if haz:
            res["raw_hazard"] = haz

        times = self._extract_timestamps(body)
        if "start_time" in times:
            res["raw_start_time"] = times["start_time"]
        if "end_time" in times:
            res["raw_end_time"] = times["end_time"]

        action = self._extract_action(body)
        if action:
            res["raw_action"] = action

        return res

    def _parse_dash_format(self, line: str) -> Dict[str, Any]:
        """Parse dash-delimited alert lines (e.g. PT-006 Kalyanpur Block 1 landslide watch - ...)."""
        res: Dict[str, Any] = {"warnings": []}
        parts = [p.strip() for p in line.split("-")]

        head = parts[0]
        match_id = re.match(r"^(PT-\d+)\s+(.*)$", head)
        if match_id:
            res["source"] = match_id.group(1)
            remainder = match_id.group(2)
        else:
            res["source"] = head
            remainder = head

        loc = self._extract_location_from_text(remainder)
        if loc:
            res["raw_location"] = loc

        sev = self._extract_known_severity(remainder)
        if sev:
            res["raw_severity"] = sev

        haz = self._extract_known_hazard(remainder)
        if haz:
            res["raw_hazard"] = haz

        if len(parts) >= 2:
            res["raw_action"] = parts[1]

        return res

    def _parse_free_text(self, line: str) -> Dict[str, Any]:
        """Parse un-structured free text alerts as fallback."""
        res: Dict[str, Any] = {"warnings": ["unsupported alert format"]}

        sev = self._extract_known_severity(line)
        if sev:
            res["raw_severity"] = sev

        haz = self._extract_known_hazard(line)
        if haz:
            res["raw_hazard"] = haz

        loc = self._extract_location_from_text(line)
        if loc:
            res["raw_location"] = loc

        return res

    def _extract_severity_and_hazard(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract raw severity and raw hazard from a combined string."""
        sev = self._extract_known_severity(text)
        if sev:
            pattern = re.compile(re.escape(sev), re.IGNORECASE)
            haz_text = pattern.sub("", text).strip()
            haz = self._extract_known_hazard(haz_text) or haz_text or None
            return sev, haz
        else:
            haz = self._extract_known_hazard(text) or text or None
            return None, haz

    def _extract_known_severity(self, text: str) -> Optional[str]:
        """Search text for known severity term."""
        for sev in self.KNOWN_SEVERITIES:
            pattern = r"\b" + re.escape(sev) + r"\b"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_known_hazard(self, text: str) -> Optional[str]:
        """Search text for known hazard term."""
        for haz in self.KNOWN_HAZARDS:
            pattern = r"\b" + re.escape(haz) + r"\b"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_location_from_text(self, text: str) -> Optional[str]:
        """Extract location name from text matching known block or district naming patterns."""
        match = re.search(
            r"\b([A-Z][a-z]+(?:\s+Block\s+\d+|\s+[A-Z][a-z]+)*)\b",
            text,
        )
        if match:
            val = match.group(1).strip()
            if val not in ["ALERT", "Duplicate", "District Control", "Malformed", "Flood", "Severe", "Cyclone"]:
                return val
        return None

    def _extract_location_after_for(self, text: str) -> Optional[str]:
        """Extract location after 'for' preposition in alert sentence."""
        match = re.search(r"\bfor\s+([A-Z][a-z]+(?:\s+Block\s+\d+)?)\b", text)
        if match:
            return match.group(1).strip()
        return None

    def _extract_timestamps(self, text: str) -> Dict[str, str]:
        """Extract start and end timestamps if present."""
        res = {}
        from_to_match = re.search(
            r"from\s+(.*?)\s+to\s+(.*?)(?:\.|$)",
            text,
            re.IGNORECASE,
        )
        if from_to_match:
            res["start_time"] = from_to_match.group(1).strip()
            res["end_time"] = from_to_match.group(2).strip()
        return res

    def _extract_action(self, text: str) -> Optional[str]:
        """Extract action instruction sentence from alert body."""
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        for part in parts:
            if re.search(
                r"\b(avoid|move|evacuate|set up|stay indoors|advised|monitor)\b",
                part,
                re.IGNORECASE,
            ):
                return part
        if len(parts) > 1:
            return parts[-1]
        return None
