"""CAP XML Alert Parser module for Alert Intelligence Engine."""

from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

from src.logger import get_logger
from src.parsers.base_parser import BaseParser
from src.schema import ParsedAlert

logger = get_logger(__name__)


class CapParser(BaseParser):
    """Parser for Common Alerting Protocol (CAP) XML disaster alerts."""

    def parse(self, raw_data: Any) -> List[ParsedAlert]:
        """Parse raw CAP XML data into a list of ParsedAlert intermediate objects.

        Args:
            raw_data: Raw input data (str, bytes, ET.ElementTree, or ET.Element).

        Returns:
            List[ParsedAlert]: List of extracted unnormalized ParsedAlert records.
        """
        alert_elements = self._normalize_input(raw_data)
        parsed_alerts: List[ParsedAlert] = []

        for index, elem in enumerate(alert_elements):
            if not isinstance(elem, ET.Element):
                logger.warning(f"Skipping record at index {index}: Expected ET.Element, got {type(elem).__name__}")
                continue

            try:
                alert = self._parse_alert_element(elem)
                parsed_alerts.append(alert)
            except Exception as e:
                logger.warning(f"Failed to parse CAP alert element at index {index}: {e}")

        return parsed_alerts

    def _normalize_input(self, raw_data: Any) -> List[ET.Element]:
        """Normalize raw input into a list of <alert> Element nodes."""
        root: Optional[ET.Element] = None

        if isinstance(raw_data, ET.ElementTree):
            root = raw_data.getroot()
        elif isinstance(raw_data, ET.Element):
            root = raw_data
        elif isinstance(raw_data, (str, bytes)):
            try:
                root = ET.fromstring(raw_data)
            except ET.ParseError as e:
                logger.warning(f"Invalid XML input string: {e}")
                return []
        else:
            logger.warning(f"Unsupported input type for CapParser: {type(raw_data).__name__}")
            return []

        if root is None:
            return []

        root_tag = self._strip_namespace(root.tag)

        if root_tag == "alerts":
            return [elem for elem in root if self._strip_namespace(elem.tag) == "alert"]
        elif root_tag == "alert":
            return [root]
        else:
            alerts = [elem for elem in root.iter() if self._strip_namespace(elem.tag) == "alert"]
            if not alerts:
                logger.warning(f"No <alert> elements found under root tag <{root.tag}>")
            return alerts

    def _parse_alert_element(self, alert_elem: ET.Element) -> ParsedAlert:
        """Extract raw fields from a single <alert> ET.Element into a ParsedAlert."""
        sender = self._get_text(alert_elem, "sender")
        source = sender if sender else "CAP Feed"

        info_elem = self._find_element(alert_elem, "info")

        raw_hazard = self._get_text(info_elem, "event") if info_elem is not None else None
        raw_severity = self._get_text(info_elem, "severity") if info_elem is not None else None
        raw_urgency = self._get_text(info_elem, "urgency") if info_elem is not None else None
        raw_certainty = self._get_text(info_elem, "certainty") if info_elem is not None else None
        raw_start_time = self._get_text(info_elem, "onset") if info_elem is not None else None
        raw_end_time = self._get_text(info_elem, "expires") if info_elem is not None else None
        raw_action = self._get_text(info_elem, "instruction") if info_elem is not None else None

        area_elem = self._find_element(info_elem, "area") if info_elem is not None else None
        raw_location = self._get_text(area_elem, "areaDesc") if area_elem is not None else None

        identifier = self._get_text(alert_elem, "identifier")

        raw_payload: Dict[str, Any] = {
            "identifier": identifier,
            "sender": sender,
            "event": raw_hazard,
            "severity": raw_severity,
            "urgency": raw_urgency,
            "certainty": raw_certainty,
            "onset": raw_start_time,
            "expires": raw_end_time,
            "areaDesc": raw_location,
            "instruction": raw_action,
        }

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
            source_format="cap_xml",
            raw_payload=raw_payload,
        )

    def _get_text(self, parent: Optional[ET.Element], tag_name: str) -> Optional[str]:
        """Private helper to safely extract text content from a child tag."""
        if parent is None:
            return None
        elem = self._find_element(parent, tag_name)
        if elem is not None and elem.text:
            text = elem.text.strip()
            return text if text else None
        return None

    def _find_element(self, parent: Optional[ET.Element], tag_name: str) -> Optional[ET.Element]:
        """Private helper to find a child element ignoring XML namespaces."""
        if parent is None:
            return None
        for child in parent:
            if self._strip_namespace(child.tag) == tag_name:
                return child
        return None

    @staticmethod
    def _strip_namespace(tag: str) -> str:
        """Strip XML namespace prefix from tag name if present."""
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag
