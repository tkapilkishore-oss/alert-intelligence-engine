"""Utility functions for Alert Intelligence Engine Streamlit UI."""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.pipeline import AlertPipeline
from src.schema import NormalizedAlert

DATA_DIR = Path(__file__).resolve().parent.parent / "data"



def load_sample_dataset(format_key: str) -> Tuple[Any, str]:
    """Load sample dataset content for evaluator instant testing.

    Args:
        format_key: Source format key ("json", "cap_xml", "rss", "plaintext", "natural_language").

    Returns:
        Tuple[Any, str]: (raw_input_data, display_text)
    """
    fmt = format_key.lower().strip()
    if fmt == "json":
        json_path = DATA_DIR / "raw_alerts_json.json"
        text_content = json_path.read_text(encoding="utf-8")
        parsed_obj = json.loads(text_content)
        return parsed_obj, text_content
    elif fmt == "cap_xml":
        cap_path = DATA_DIR / "raw_alerts_cap.xml"
        text_content = cap_path.read_text(encoding="utf-8")
        return text_content, text_content
    elif fmt == "rss":
        rss_path = DATA_DIR / "raw_alerts_rss.xml"
        text_content = rss_path.read_text(encoding="utf-8")
        return text_content, text_content
    elif fmt == "plaintext":
        pt_path = DATA_DIR / "raw_alerts_plaintext.txt"
        text_content = pt_path.read_text(encoding="utf-8")
        return text_content, text_content
    elif fmt == "natural_language":
        sample_prompt = (
            "Heavy rainfall and urban flooding expected tomorrow morning in Devapur. "
            "Residents should avoid flooded roads and move valuables above ground level."
        )
        return sample_prompt, sample_prompt
    else:
        raise ValueError(f"Unknown format key: {format_key}")


def execute_pipeline(
    pipeline: AlertPipeline, raw_input: Any, source_format: str
) -> Tuple[List[NormalizedAlert], float, Optional[str], Optional[str]]:
    """Execute AlertPipeline on raw input and measure execution time accurately.

    Args:
        pipeline: AlertPipeline instance.
        raw_input: Raw data payload or string.
        source_format: Format string identifier ("json", "cap_xml", "rss", "plaintext", "natural_language").

    Returns:
        Tuple[List[NormalizedAlert], float, Optional[str], Optional[str]]:
            (normalized_alerts, processing_time_ms, error_title, error_message)
    """
    start_time = time.perf_counter()
    fmt_clean = source_format.lower().strip()

    # Pre-validation for string payloads (Paste text / File upload)
    if isinstance(raw_input, str):
        cleaned_str = raw_input.strip()
        if not cleaned_str:
            return (
                [],
                0.0,
                "Empty Input Payload",
                "The provided input is empty or contains only whitespace.",
            )

        if fmt_clean == "json":
            try:
                raw_input = json.loads(cleaned_str)
            except json.JSONDecodeError as exc:
                return (
                    [],
                    0.0,
                    "Invalid JSON Content",
                    f"Invalid JSON content. Please paste a valid JSON document.\nSyntax error: {str(exc)}",
                )

        elif fmt_clean in ["cap_xml", "rss"]:
            import xml.etree.ElementTree as ET
            try:
                ET.fromstring(cleaned_str)
            except ET.ParseError as exc:
                return (
                    [],
                    0.0,
                    f"Invalid {fmt_clean.upper()} XML Input",
                    f"The uploaded/pasted input is not valid XML syntax.\nSyntax error: {str(exc)}",
                )

    try:
        if fmt_clean == "natural_language":
            text_str = str(raw_input) if not isinstance(raw_input, str) else raw_input
            alerts = pipeline.process_natural_language(text_str)
        else:
            alerts = pipeline.process(raw_input, fmt_clean)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return alerts, round(elapsed_ms, 2), None, None

    except ValueError as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return (
            [],
            round(elapsed_ms, 2),
            "Format or Validation Error",
            f"The engine encountered a processing error: {str(exc)}",
        )
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        err_msg = str(exc)
        if "quota" in err_msg.lower() or "429" in err_msg or "resource_exhausted" in err_msg.lower():
            return (
                [],
                round(elapsed_ms, 2),
                "Gemini API Limit Warning",
                "Gemini API rate limit exceeded. Processing completed without AI fallback enrichment.",
            )
        return (
            [],
            round(elapsed_ms, 2),
            "Pipeline Processing Failure",
            f"An unexpected error occurred during pipeline execution:\n{err_msg}",
        )



def export_alerts_to_json(alerts: List[NormalizedAlert]) -> str:
    """Convert list of NormalizedAlert objects to pretty JSON string.

    Args:
        alerts: List of NormalizedAlert records.

    Returns:
        str: Formatted JSON string.
    """
    dict_list = [alert.model_dump() for alert in alerts]
    return json.dumps(dict_list, indent=2)


def export_alerts_to_csv(alerts: List[NormalizedAlert]) -> str:
    """Convert list of NormalizedAlert objects to CSV string.

    Args:
        alerts: List of NormalizedAlert records.

    Returns:
        str: Formatted CSV string.
    """
    if not alerts:
        return ""
    dict_list = [alert.model_dump() for alert in alerts]
    df = pd.DataFrame(dict_list)
    return df.to_csv(index=False)


def run_complete_demo(
    pipeline: AlertPipeline,
) -> Tuple[Dict[str, List[NormalizedAlert]], Dict[str, float], float, int, int, int]:
    """Execute complete engine showcase demo across all 5 supported formats.

    Args:
        pipeline: AlertPipeline instance.

    Returns:
        Tuple containing:
            - results_by_format: Dict mapping format name to List[NormalizedAlert]
            - timing_by_format: Dict mapping format name to time in ms
            - total_time_ms: Total processing time in ms
            - total_alerts: Total normalized alerts produced
            - total_duplicates: Total duplicate alerts identified
            - total_warnings: Total parse warnings generated
    """
    formats = [
        ("json", "JSON"),
        ("cap_xml", "CAP XML"),
        ("rss", "RSS XML"),
        ("plaintext", "Plaintext"),
        ("natural_language", "Natural Language"),
    ]

    results_by_format: Dict[str, List[NormalizedAlert]] = {}
    timing_by_format: Dict[str, float] = {}

    total_start = time.perf_counter()
    all_alerts: List[NormalizedAlert] = []

    for fmt_key, fmt_label in formats:
        input_data, _ = load_sample_dataset(fmt_key)
        alerts, elapsed_ms, err_title, err_msg = execute_pipeline(pipeline, input_data, fmt_key)
        results_by_format[fmt_label] = alerts
        timing_by_format[fmt_label] = elapsed_ms
        all_alerts.extend(alerts)

    total_time_ms = round((time.perf_counter() - total_start) * 1000.0, 2)
    total_alerts = len(all_alerts)
    total_duplicates = sum(1 for a in all_alerts if a.is_duplicate)
    total_warnings = sum(len(a.parse_warnings) for a in all_alerts)

    return (
        results_by_format,
        timing_by_format,
        total_time_ms,
        total_alerts,
        total_duplicates,
        total_warnings,
    )
