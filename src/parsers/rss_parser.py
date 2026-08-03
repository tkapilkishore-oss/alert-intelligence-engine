"""RSS XML Alert Parser module for Alert Intelligence Engine."""

import re
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

from src.logger import get_logger
from src.parsers.base_parser import BaseParser
from src.schema import ParsedAlert

logger = get_logger(__name__)


class RssParser(BaseParser):
    """Parser for RSS XML disaster alert feeds."""

    _TITLE_HAZARD_LOC_PATTERN = re.compile(
        r"^(?:.+?:\s*)?(?P<hazard>.+?)\s+(?:warning|alert|advisory)\s+for\s+(?P<location>.+)$",
        re.IGNORECASE,
    )
    _ACTION_PATTERN = re.compile(
        r"Action:\s*(?P<action>.*?)(?:\.\s*Valid|\.|$)",
        re.IGNORECASE,
    )

    def parse(self, raw_data: Any) -> List[ParsedAlert]:
        """Parse raw RSS XML data into a list of ParsedAlert intermediate objects.

        Args:
            raw_data: Raw input data (str, bytes, ET.ElementTree, ET.Element, or List[ET.Element]).

        Returns:
            List[ParsedAlert]: List of extracted unnormalized ParsedAlert records.
        """
        channel_title, item_elements = self._normalize_input(raw_data)
        parsed_alerts: List[ParsedAlert] = []

        for index, elem in enumerate(item_elements):
            if not isinstance(elem, ET.Element):
                logger.warning(f"Skipping record at index {index}: Expected ET.Element, got {type(elem).__name__}")
                continue

            try:
                alert = self._parse_item_element(elem, channel_title)
                parsed_alerts.append(alert)
            except Exception as e:
                logger.warning(f"Failed to parse RSS item element at index {index}: {e}")

        return parsed_alerts

    def _normalize_input(self, raw_data: Any) -> Tuple[Optional[str], List[ET.Element]]:
        """Normalize raw input into channel title and a list of <item> Element nodes."""
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
                return None, []
        elif isinstance(raw_data, list):
            item_nodes = [elem for elem in raw_data if isinstance(elem, ET.Element) and self._strip_namespace(elem.tag) == "item"]
            return None, item_nodes
        else:
            logger.warning(f"Unsupported input type for RssParser: {type(raw_data).__name__}")
            return None, []

        if root is None:
            return None, []

        root_tag = self._strip_namespace(root.tag)

        channel_title: Optional[str] = None
        channel_elem: Optional[ET.Element] = None

        if root_tag == "rss":
            channel_elem = self._find_element(root, "channel")
        elif root_tag == "channel":
            channel_elem = root

        if channel_elem is not None:
            channel_title = self._get_text(channel_elem, "title")

        if channel_elem is not None:
            items = [elem for elem in channel_elem if self._strip_namespace(elem.tag) == "item"]
        elif root_tag == "item":
            items = [root]
        else:
            items = [elem for elem in root.iter() if self._strip_namespace(elem.tag) == "item"]
            if not items:
                logger.warning(f"No <item> elements found under root tag <{root.tag}>")

        return channel_title, items

    def _parse_item_element(self, item_elem: ET.Element, channel_title: Optional[str]) -> ParsedAlert:
        """Extract raw fields from a single <item> ET.Element into a ParsedAlert."""
        title = self._get_text(item_elem, "title")
        description = self._get_text(item_elem, "description")
        pub_date = self._get_text(item_elem, "pubDate")
        guid = self._get_text(item_elem, "guid")
        link = self._get_text(item_elem, "link")
        category = self._get_text(item_elem, "category")

        if not title and not description:
            raise ValueError("RSS item element missing both title and description")

        source = channel_title if channel_title else "RSS Feed"

        raw_severity, raw_hazard, raw_location = self._extract_title_metadata(title)
        raw_action = self._extract_description_action(description)
        raw_start_time = pub_date

        raw_payload: Dict[str, Any] = {
            "guid": guid,
            "title": title,
            "description": description,
            "pubDate": pub_date,
        }
        if link:
            raw_payload["link"] = link
        if category:
            raw_payload["category"] = category

        return ParsedAlert(
            raw_hazard=raw_hazard,
            raw_severity=raw_severity,
            raw_urgency=None,
            raw_certainty=None,
            raw_location=raw_location,
            raw_start_time=raw_start_time,
            raw_end_time=None,
            raw_action=raw_action,
            source=source,
            source_format="rss",
            raw_payload=raw_payload,
        )

    def _extract_title_metadata(self, title: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract raw severity, hazard, and location metadata from item title string."""
        if not title:
            return None, None, None

        raw_severity: Optional[str] = None
        raw_hazard: Optional[str] = None
        raw_location: Optional[str] = None

        if ":" in title:
            prefix, remainder = title.split(":", 1)
            raw_severity = prefix.strip()

        match = self._TITLE_HAZARD_LOC_PATTERN.match(title)
        if match:
            raw_hazard = match.group("hazard").strip()
            raw_location = match.group("location").strip()
        else:
            raw_hazard = title

        return raw_severity, raw_hazard, raw_location

    def _extract_description_action(self, description: Optional[str]) -> Optional[str]:
        """Extract raw recommended action from item description string."""
        if not description:
            return None

        match = self._ACTION_PATTERN.search(description)
        if match:
            return match.group("action").strip()

        return None

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
