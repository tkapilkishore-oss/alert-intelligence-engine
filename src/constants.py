"""Project-wide constant definitions for Alert Intelligence Engine."""

from pathlib import Path

# Base Directories
BASE_DIR: Path = Path(__file__).resolve().parent.parent
_provided_dir = BASE_DIR / "data" / "provided"
DATA_DIR: Path = _provided_dir if _provided_dir.exists() else BASE_DIR / "data"
DOCS_DIR: Path = BASE_DIR / "docs"
OUTPUTS_DIR: Path = BASE_DIR / "outputs"

# Source Formats
SUPPORTED_SOURCE_FORMATS: tuple[str, ...] = ("json", "cap_xml", "rss", "plaintext")

# File Defaults
DEFAULT_OUTPUT_FILENAME: str = "normalized_alerts.json"
DEFAULT_OUTPUT_PATH: Path = OUTPUTS_DIR / DEFAULT_OUTPUT_FILENAME

# Reference Data Files
SEVERITY_REFERENCE_FILE: Path = DATA_DIR / "severity_mapping_reference.csv"
LOCATION_REFERENCE_FILE: Path = DATA_DIR / "location_reference.csv"
EXPECTED_SCHEMA_FILE: Path = DATA_DIR / "expected_normalized_schema.json"

# Global Thresholds & Engine Settings
DEDUPLICATION_THRESHOLD: float = 0.75

# Logging Constants
DEFAULT_LOG_NAME: str = "alert_intelligence_engine"
DEFAULT_LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
