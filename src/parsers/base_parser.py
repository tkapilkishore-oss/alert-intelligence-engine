"""Abstract parser base class for format-specific alert parsers."""

from abc import ABC, abstractmethod
from typing import Any, List
from src.schema import ParsedAlert


class BaseParser(ABC):
    """Abstract interface implemented by all format-specific alert parsers."""

    @abstractmethod
    def parse(self, raw_data: Any) -> List[ParsedAlert]:
        """Parse format-specific raw alert input and return intermediate ParsedAlert records.

        Args:
            raw_data: Raw input data (dict, string, XML root element, etc.).

        Returns:
            List[ParsedAlert]: List of extracted unnormalized ParsedAlert objects.
        """
        pass
