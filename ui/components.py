"""UI components for Alert Intelligence Engine Streamlit Dashboard."""

import json
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from src.schema import NormalizedAlert
from ui.styles import get_duplicate_badge_html, get_severity_badge_html
from ui.utils import export_alerts_to_csv, export_alerts_to_json


def render_hero_header() -> None:
    """Render top hero header with status badges."""
    st.markdown(
        """
    <div class="hero-container">
        <div class="hero-title">
            <span>🛡️ Alert Intelligence Engine</span>
        </div>
        <div class="hero-subtitle">
            Standardized Disaster Alert Parsing, Normalization & Deduplication Engine
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
            <span class="status-pill">● Engine Status: READY</span>
            <span class="badge badge-format">Pipeline Version: v1.0.0</span>
            <span class="badge badge-canonical">Supported Formats: JSON | CAP XML | RSS | Plaintext | Natural Language</span>
            <span class="badge badge-minor">Tests: 123 Passed</span>
            <span class="badge badge-moderate">Architecture: 12 Frozen Stages</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> Tuple[str, str, Any]:
    """Render sidebar control panel.

    Returns:
        Tuple[str, str, Any]: (source_format, input_method, raw_input_data)
    """
    st.sidebar.markdown("### ⚙️ Engine Control Panel")
    st.sidebar.markdown("---")

    # Input Method Selection
    input_method = st.sidebar.radio(
        "Select Input Method",
        options=[
            "Load Sample Dataset",
            "Upload JSON Content",
            "Plain Text",
            "Upload File",
        ],
        index=0,
    )

    source_format = "json"
    raw_input_data: Any = None

    if input_method == "Load Sample Dataset":
        sample_format_options = {
            "JSON": "json",
            "CAP XML": "cap_xml",
            "RSS XML": "rss",
            "Plaintext": "plaintext",
            "Natural Language": "natural_language",
        }
        selected_sample_label = st.sidebar.selectbox(
            "Select Sample Dataset Format",
            options=list(sample_format_options.keys()),
            index=0,
            help="Choose the sample format to load into the pipeline.",
        )
        source_format = sample_format_options[selected_sample_label]
        st.sidebar.info(f"Loaded sample dataset for **{selected_sample_label}**.")

    elif input_method == "Upload JSON Content":
        source_format = "json"
        raw_input_data = st.sidebar.text_area(
            "Paste Raw JSON Content",
            height=200,
            placeholder='Paste raw JSON document here...\n\nExample:\n{\n  "alert_id": "ALT-101",\n  "headline": "Severe Flood Warning",\n  ...\n}',
            help="Strict JSON input only. Must be a valid JSON object or array.",
        )

    elif input_method == "Plain Text":
        source_format = "natural_language"
        raw_input_data = st.sidebar.text_area(
            "Enter Plain Text / Emergency Prompt",
            height=200,
            placeholder="Type or paste natural English alert description here...\n\nExample:\nHeavy rainfall warning for Devapur from tomorrow morning. Residents should avoid flooded roads.",
            help="Unrestricted natural English text input.",
        )

    elif input_method == "Upload File":
        file_format_options = {
            "JSON": "json",
            "CAP XML": "cap_xml",
            "RSS XML": "rss",
            "Plaintext": "plaintext",
        }
        selected_file_label = st.sidebar.selectbox(
            "Select File Format",
            options=list(file_format_options.keys()),
            index=0,
            help="Select the format of the file you are uploading.",
        )
        source_format = file_format_options[selected_file_label]
        uploaded_file = st.sidebar.file_uploader(
            "Upload Alert File",
            type=["json", "xml", "rss", "txt"],
        )
        if uploaded_file is not None:
            content = uploaded_file.read().decode("utf-8")
            if source_format == "json":
                try:
                    raw_input_data = json.loads(content)
                except json.JSONDecodeError:
                    raw_input_data = content  # execute_pipeline catches error cleanly
            else:
                raw_input_data = content

    st.sidebar.markdown("---")
    return source_format, input_method, raw_input_data


def render_summary_metrics(
    alerts: List[NormalizedAlert],
    elapsed_ms: float,
    source_format_label: str,
) -> None:
    """Render KPI metrics bar.

    Args:
        alerts: List of processed NormalizedAlert records.
        elapsed_ms: Execution time in milliseconds.
        source_format_label: Label of source format processed.
    """
    total_alerts = len(alerts)
    total_duplicates = sum(1 for a in alerts if a.is_duplicate)
    total_warnings = sum(len(a.parse_warnings) for a in alerts)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title">Alerts Processed</div>
            <div class="kpi-value">{total_alerts}</div>
            <div class="kpi-subtext">Normalized schema records</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title">Duplicates Detected</div>
            <div class="kpi-value" style="color: {'#F87171' if total_duplicates > 0 else '#34D399'};">{total_duplicates}</div>
            <div class="kpi-subtext">Weighted score ≥ 0.75</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title">Parse Warnings</div>
            <div class="kpi-value" style="color: {'#FBBF24' if total_warnings > 0 else '#34D399'};">{total_warnings}</div>
            <div class="kpi-subtext">Graceful warning records</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title">Processing Time</div>
            <div class="kpi-value" style="color: #38BDF8;">{elapsed_ms:.1f} <span style="font-size: 1rem;">ms</span></div>
            <div class="kpi-subtext">Pipeline execution speed</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col5:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title">Source Format</div>
            <div class="kpi-value" style="font-size: 1.25rem; color: #C084FC; margin-top: 4px;">{source_format_label.upper()}</div>
            <div class="kpi-subtext">Active parser stream</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_filter_and_search_controls(alerts: List[NormalizedAlert]) -> List[NormalizedAlert]:
    """Render presentation-only filter and search bar.

    Args:
        alerts: List of processed NormalizedAlert records.

    Returns:
        List[NormalizedAlert]: Filtered list for display (does not mutate engine output).
    """
    if not alerts:
        return []

    st.markdown("#### 🔍 Search & Presentation Filters")
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

    with col1:
        search_query = st.text_input(
            "Search Alerts",
            placeholder="Search Alert ID, Location, or Hazard...",
            key="search_input",
        ).strip().lower()

    # Extract unique options for dropdowns
    hazards = sorted(list(set(a.hazard_type for a in alerts)))
    severities = sorted(list(set(a.severity for a in alerts)))

    hazard_options = ["All"] + hazards
    severity_options = ["All"] + severities
    dup_options = ["All", "Canonical Only", "Duplicates Only"]

    if "filter_hazard" in st.session_state and st.session_state.filter_hazard not in hazard_options:
        st.session_state.filter_hazard = "All"
    if "filter_severity" in st.session_state and st.session_state.filter_severity not in severity_options:
        st.session_state.filter_severity = "All"
    if "filter_duplicate" in st.session_state and st.session_state.filter_duplicate not in dup_options:
        st.session_state.filter_duplicate = "All"

    with col2:
        selected_hazard = st.selectbox(
            "Hazard Type",
            options=hazard_options,
            key="filter_hazard",
        )

    with col3:
        selected_severity = st.selectbox(
            "Severity Level",
            options=severity_options,
            key="filter_severity",
        )

    with col4:
        selected_dup = st.selectbox(
            "Duplicate Status",
            options=dup_options,
            key="filter_duplicate",
        )

    filtered = list(alerts)

    # Apply Search
    if search_query:
        filtered = [
            a for a in filtered
            if search_query in a.alert_id.lower()
            or search_query in a.hazard_type.lower()
            or search_query in (a.location_name or "").lower()
            or search_query in (a.recommended_action or "").lower()
        ]

    # Apply Hazard Filter
    if selected_hazard != "All":
        filtered = [a for a in filtered if a.hazard_type == selected_hazard]

    # Apply Severity Filter
    if selected_severity != "All":
        filtered = [a for a in filtered if a.severity == selected_severity]

    # Apply Duplicate Filter
    if selected_dup == "Canonical Only":
        filtered = [a for a in filtered if not a.is_duplicate]
    elif selected_dup == "Duplicates Only":
        filtered = [a for a in filtered if a.is_duplicate]

    st.caption(f"Showing **{len(filtered)}** of **{len(alerts)}** alerts")
    return filtered


def render_results_cards(alerts: List[NormalizedAlert]) -> None:
    """Render Executive Alert Cards.

    Args:
        alerts: List of NormalizedAlert records to display.
    """
    if not alerts:
        st.info("No alerts match the selected search or filter criteria.")
        return

    for idx, alert in enumerate(alerts, 1):
        sev_badge = get_severity_badge_html(alert.severity)
        dup_badge = get_duplicate_badge_html(alert.is_duplicate)
        hazard_title = alert.hazard_type.replace("_", " ").title()
        loc_name = alert.location_name or "Unknown Location"

        header_text = f"Alert #{idx}: {alert.alert_id} | {hazard_title} ({loc_name})"

        with st.expander(f"{header_text}", expanded=(idx == 1)):
            st.markdown(
                f"""
            <div style="display: flex; gap: 12px; margin-bottom: 12px; align-items: center;">
                <strong>Severity:</strong> {sev_badge}
                <strong>Status:</strong> {dup_badge}
                <span class="badge badge-format">Source: {alert.source_format.upper()}</span>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Alert ID:** `{alert.alert_id}`")
                st.markdown(f"**Source Agency:** `{alert.source}`")
                st.markdown(f"**Hazard Type:** `{alert.hazard_type}`")
                st.markdown(f"**Severity:** `{alert.severity}`")
                st.markdown(f"**Urgency:** `{alert.urgency}`")
                st.markdown(f"**Certainty:** `{alert.certainty}`")

            with col2:
                st.markdown(f"**Location:** `{loc_name}` (ID: `{alert.location_id}`) ")
                st.markdown(f"**Start Time:** `{alert.start_time or 'N/A'}`")
                st.markdown(f"**End Time:** `{alert.end_time or 'N/A'}`")
                st.markdown(f"**Is Duplicate:** `{alert.is_duplicate}`")
                st.markdown(f"**Recommended Action:** {alert.recommended_action}")

            if alert.parse_warnings:
                st.warning("⚠️ **Parse Warnings:**\n" + "\n".join(f"- {w}" for w in alert.parse_warnings))
            else:
                st.success("✅ Clean parsing — zero warnings recorded.")


def render_results_table(alerts: List[NormalizedAlert]) -> None:
    """Render Compact Data Table view.

    Args:
        alerts: List of NormalizedAlert records to display.
    """
    if not alerts:
        st.info("No alerts match the selected search or filter criteria.")
        return

    data = []
    for alert in alerts:
        row = alert.model_dump()
        row["parse_warnings"] = "; ".join(alert.parse_warnings) if alert.parse_warnings else "None"
        data.append(row)

    df = pd.DataFrame(data)

    # Reorder columns for readability
    column_order = [
        "alert_id",
        "hazard_type",
        "severity",
        "urgency",
        "certainty",
        "location_name",
        "location_id",
        "is_duplicate",
        "parse_warnings",
        "start_time",
        "end_time",
        "recommended_action",
        "source",
        "source_format",
    ]
    existing_cols = [c for c in column_order if c in df.columns]
    df = df[existing_cols]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        key="results_data_table",
    )


def render_raw_json_and_downloads(alerts: List[NormalizedAlert]) -> None:
    """Render Raw JSON viewer and Download buttons.

    Args:
        alerts: List of NormalizedAlert records.
    """
    if not alerts:
        st.info("No processed alerts available for download.")
        return

    col1, col2 = st.columns(2)
    json_data = export_alerts_to_json(alerts)
    csv_data = export_alerts_to_csv(alerts)

    with col1:
        st.download_button(
            label="📥 Download Normalized JSON",
            data=json_data,
            file_name="normalized_alerts.json",
            mime="application/json",
            use_container_width=True,
        )

    with col2:
        st.download_button(
            label="📊 Download Normalized CSV",
            data=csv_data,
            file_name="normalized_alerts.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("#### 📄 Complete Normalized JSON Output")
    st.json(json_data)


def render_pipeline_tab(active_format: str) -> None:
    """Render graphical representation of pipeline flow using Streamlit container boxes.

    Args:
        active_format: Currently selected source format ("json", "cap_xml", "rss", "plaintext", "natural_language").
    """
    st.markdown("### 🔄 Engine Pipeline Execution Flow")
    st.markdown(
        "Below is the exact 7-stage architectural workflow executed by `AlertPipeline`."
    )

    fmt_clean = (active_format or "json").lower().strip()
    is_gemini_active = fmt_clean in ["plaintext", "natural_language"]

    steps = [
        ("1. Input Ingestion", f"Format Stream: {active_format.upper()}", False),
        ("2. Format Parser Router", f"Target Parser: {active_format.upper()} Parser", True),
        ("3. Structural Validation", "Validate minimum usable fields & structure", False),
        ("4. Gemini Fallback Engine", "AI Enrichment (Plaintext / Incomplete inputs)", is_gemini_active),
        ("5. Normalization Engine", "Map Severity, Urgency, Certainty & Location IDs", False),
        ("6. Schema Validation", "Validate final Pydantic NormalizedAlert schema", False),
        ("7. Deduplication Engine", "Weighted similarity scoring (Threshold ≥ 0.75)", False),
        ("Output Deliverable", "normalized_alerts.json", False),
    ]

    for idx, (title, desc, is_active_fmt) in enumerate(steps):
        box_class = "pipeline-step-box"
        if is_active_fmt:
            box_class += " active-format"
        elif "Gemini" in title and is_gemini_active:
            box_class += " active-gemini"

        st.markdown(
            f"""
        <div class="{box_class}">
            <div style="font-weight: 700; color: #F8FAFC; font-size: 1.05rem;">{title}</div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">{desc}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if idx < len(steps) - 1:
            st.markdown(
                '<div style="text-align: center; color: #38BDF8; font-weight: bold; font-size: 1.2rem; margin: -4px 0;">↓</div>',
                unsafe_allow_html=True,
            )


def render_about_tab() -> None:
    """Render About Tab with engine specifications."""
    st.markdown("### 📖 About Alert Intelligence Engine v1.0.0")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
        #### 🏛️ System Architecture Summary
        The Alert Intelligence Engine is a high-performance disaster alert normalization system designed for Emergency Operations Centers (EOCs) and public safety platforms.
        
        - **Pipeline Pattern:** Sequential 7-stage processing pipeline.
        - **Deterministic First:** 100% deterministic parsing and rule-based normalization.
        - **AI Fallback:** Google Gemini API utilized strictly as a fallback for incomplete plaintext extraction.
        - **Deduplication:** Multi-factor weighted score (35% Hazard, 30% Location, 20% Time, 15% Text).
        """
        )

    with col2:
        st.markdown(
            """
        #### 🧰 Technical Stack
        - **Core Language:** Python 3.11+ / 3.14
        - **Data Validation:** Pydantic v2
        - **XML & Feeds:** `lxml`, `feedparser`
        - **Data & Matching:** `pandas`, `RapidFuzz`
        - **AI Fallback:** Google Gemini API (`google-genai`)
        - **Testing:** `pytest` (123 test cases passing)
        - **UI Client:** Streamlit Presentation Layer
        """
        )

    st.markdown("---")
    st.markdown("#### 🚀 Implemented Stages (Stages 1–12 Complete & Frozen)")

    stages_data = [
        {"Stage": "Stage 1", "Module": "Project Foundation & Schemas", "Status": "FROZEN"},
        {"Stage": "Stage 2", "Module": "JSON Parser", "Status": "FROZEN"},
        {"Stage": "Stage 3", "Module": "CAP XML Parser", "Status": "FROZEN"},
        {"Stage": "Stage 4", "Module": "RSS XML Parser", "Status": "FROZEN"},
        {"Stage": "Stage 5", "Module": "Plaintext Parser", "Status": "FROZEN"},
        {"Stage": "Stage 6", "Module": "Gemini Fallback Engine", "Status": "FROZEN"},
        {"Stage": "Stage 7", "Module": "Normalization Engine & Mappers", "Status": "FROZEN"},
        {"Stage": "Stage 8", "Module": "Validation Engine", "Status": "FROZEN"},
        {"Stage": "Stage 9", "Module": "Deduplication Engine", "Status": "FROZEN"},
        {"Stage": "Stage 10", "Module": "Pipeline Orchestration Engine", "Status": "FROZEN"},
        {"Stage": "Stage 11", "Module": "End-to-End Verification Suite", "Status": "FROZEN"},
        {"Stage": "Stage 12", "Module": "NLP Entry Layer & Release v1.0.0", "Status": "RELEASED"},
    ]
    st.table(pd.DataFrame(stages_data))


def render_empty_state() -> None:
    """Render empty state landing page."""
    st.markdown(
        """
    <div class="landing-card">
        <h2>⚡ Ready to Process Disaster Alerts</h2>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Select an input method from the sidebar or click <strong>Run Complete Demo</strong> to test all formats instantly.
        </p>
        <hr style="border-color: #334155; margin: 20px 0;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px;">
            <div style="background: rgba(255,255,255,0.03); border: 1px solid #334155; padding: 16px; border-radius: 8px;">
                <h4 style="color: #38BDF8; margin-bottom: 6px;">1. Select Input Stream</h4>
                <p style="font-size: 0.85rem; color: #CBD5E1;">Choose JSON, CAP XML, RSS XML, Plaintext, or Natural Language prompt.</p>
            </div>
            <div style="background: rgba(255,255,255,0.03); border: 1px solid #334155; padding: 16px; border-radius: 8px;">
                <h4 style="color: #34D399; margin-bottom: 6px;">2. Load Sample or Paste</h4>
                <p style="font-size: 0.85rem; color: #CBD5E1;">Use pre-packaged assignment datasets or upload your own files.</p>
            </div>
            <div style="background: rgba(255,255,255,0.03); border: 1px solid #334155; padding: 16px; border-radius: 8px;">
                <h4 style="color: #C084FC; margin-bottom: 6px;">3. Process & Export</h4>
                <p style="font-size: 0.85rem; color: #CBD5E1;">View executive cards, data table, pipeline metrics, and download JSON/CSV.</p>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_error_panel(title: str, message: str) -> None:
    """Render styled error panel for invalid inputs.

    Args:
        title: Short title for error.
        message: Detailed explanation message.
    """
    st.markdown(
        f"""
    <div class="error-panel">
        <h4 style="margin-bottom: 8px; color: #EF4444;">❌ {title}</h4>
        <div style="white-space: pre-wrap; font-family: monospace; font-size: 0.9rem;">{message}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render footer element."""
    st.markdown(
        """
    <div class="dashboard-footer">
        Alert Intelligence Engine — Version 1.0.0 | Powered by Python, Streamlit, Google Gemini, Pydantic
    </div>
    """,
        unsafe_allow_html=True,
    )
