"""Alert Intelligence Engine — Streamlit Presentation Layer Application.

Strict presentation layer over frozen engine stages 1-12.
Exclusively calls AlertPipeline.process(...) and AlertPipeline.process_natural_language(...).
"""

import os
from typing import Any, Dict, List, Optional

import streamlit as st

from src.pipeline import AlertPipeline
from src.schema import NormalizedAlert
from ui.components import (
    render_about_tab,
    render_empty_state,
    render_error_panel,
    render_filter_and_search_controls,
    render_footer,
    render_hero_header,
    render_pipeline_tab,
    render_raw_json_and_downloads,
    render_results_cards,
    render_results_table,
    render_sidebar,
    render_summary_metrics,
)
from ui.styles import MAIN_CSS
from ui.utils import execute_pipeline, load_sample_dataset, run_complete_demo

# Page Configuration
st.set_page_config(
    page_title="Alert Intelligence Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Custom CSS
st.markdown(MAIN_CSS, unsafe_allow_html=True)

# Streamlit Community Cloud Secrets Bridge (Production-Safe)
try:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        secret_key = st.secrets.get("GEMINI_API_KEY")
        if secret_key and not os.getenv("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = str(secret_key)
except Exception:
    # Secrets file or secrets dictionary not present in environment; safe fallback
    pass


@st.cache_resource
def get_pipeline() -> AlertPipeline:


    """Instantiate and cache single AlertPipeline instance.

    Returns:
        AlertPipeline: Engine pipeline instance.
    """
    return AlertPipeline()


def main() -> None:
    """Main application orchestrator."""
    pipeline = get_pipeline()

    # Session State Initialization
    if "processed_alerts" not in st.session_state:
        st.session_state.processed_alerts = None
    if "elapsed_ms" not in st.session_state:
        st.session_state.elapsed_ms = 0.0
    if "source_format_label" not in st.session_state:
        st.session_state.source_format_label = "JSON"
    if "active_format_key" not in st.session_state:
        st.session_state.active_format_key = "json"
    if "error_info" not in st.session_state:
        st.session_state.error_info = None
    if "demo_summary" not in st.session_state:
        st.session_state.demo_summary = None

    # Render Hero Header
    render_hero_header()

    # Render Sidebar & Get Controls
    source_format_key, input_method, raw_input_data = render_sidebar()

    format_labels = {
        "json": "JSON",
        "cap_xml": "CAP XML",
        "rss": "RSS XML",
        "plaintext": "Plaintext",
        "natural_language": "Natural Language",
    }
    current_label = format_labels.get(source_format_key, source_format_key.upper())

    # Sidebar Action Buttons
    col_btn1, col_btn2 = st.sidebar.columns([1, 1])
    process_clicked = col_btn1.button("⚡ Process", type="primary", use_container_width=True)
    demo_clicked = col_btn2.button("🚀 Demo Mode", use_container_width=True)

    # Process Action Handler
    if process_clicked:
        st.session_state.demo_summary = None
        st.session_state.search_input = ""
        st.session_state.filter_hazard = "All"
        st.session_state.filter_severity = "All"
        st.session_state.filter_duplicate = "All"
        input_payload: Any = None

        if input_method == "Load Sample Dataset":
            input_payload, _ = load_sample_dataset(source_format_key)
        else:
            input_payload = raw_input_data

        if input_payload is None or (isinstance(input_payload, str) and not input_payload.strip()):
            st.session_state.processed_alerts = None
            st.session_state.error_info = (
                "Empty Input Payload",
                "Please enter text, upload a file, or select 'Load Sample Dataset'.",
            )
        else:
            alerts, elapsed_ms, err_title, err_msg = execute_pipeline(
                pipeline, input_payload, source_format_key
            )
            if err_title:
                st.session_state.processed_alerts = None
                st.session_state.error_info = (err_title, err_msg)
            else:
                st.session_state.processed_alerts = alerts
                st.session_state.elapsed_ms = elapsed_ms
                st.session_state.source_format_label = current_label
                st.session_state.active_format_key = source_format_key
                st.session_state.error_info = None

    # Demo Mode Action Handler
    if demo_clicked:
        st.session_state.search_input = ""
        st.session_state.filter_hazard = "All"
        st.session_state.filter_severity = "All"
        st.session_state.filter_duplicate = "All"
        with st.spinner("Executing complete demo across all 5 engine formats..."):
            (
                results_by_format,
                timing_by_format,
                total_time_ms,
                total_alerts,
                total_duplicates,
                total_warnings,
            ) = run_complete_demo(pipeline)

            all_combined_alerts: List[NormalizedAlert] = []
            for alerts_list in results_by_format.values():
                all_combined_alerts.extend(alerts_list)

            st.session_state.processed_alerts = all_combined_alerts
            st.session_state.elapsed_ms = total_time_ms
            st.session_state.source_format_label = "ALL FORMATS (DEMO)"
            st.session_state.active_format_key = "json"
            st.session_state.error_info = None
            st.session_state.demo_summary = {
                "results_by_format": results_by_format,
                "timing_by_format": timing_by_format,
                "total_alerts": total_alerts,
                "total_duplicates": total_duplicates,
                "total_warnings": total_warnings,
            }

    # Render Error Panels (if any)
    if st.session_state.error_info:
        err_title, err_msg = st.session_state.error_info
        render_error_panel(err_title, err_msg)

    # Render Demo Showcase Banner (if active)
    if st.session_state.demo_summary:
        demo = st.session_state.demo_summary
        st.success(
            f"🎉 **Demo Execution Complete!** Processed **{demo['total_alerts']} alerts** "
            f"across 5 formats in **{st.session_state.elapsed_ms:.1f} ms** "
            f"({demo['total_duplicates']} duplicates flagged, {demo['total_warnings']} warnings)."
        )

    # Main Tab Layout
    tab_cards, tab_table, tab_json, tab_flow, tab_about = st.tabs(
        [
            "🟨 Executive Cards",
            "📊 Data Table",
            "📄 Raw JSON & Exports",
            "🔄 Pipeline Execution Flow",
            "📖 About Engine",
        ]
    )

    alerts = st.session_state.processed_alerts

    if alerts is not None:
        # Presentation Filters & Search
        filtered_alerts = render_filter_and_search_controls(alerts)

        # Render Metrics Bar from filtered_alerts
        render_summary_metrics(
            filtered_alerts,
            st.session_state.elapsed_ms,
            st.session_state.source_format_label,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        with tab_cards:
            render_results_cards(filtered_alerts)

        with tab_table:
            render_results_table(filtered_alerts)

        with tab_json:
            render_raw_json_and_downloads(filtered_alerts)

        with tab_flow:
            render_pipeline_tab(st.session_state.active_format_key)

        with tab_about:
            render_about_tab()

    else:
        with tab_cards:
            render_empty_state()
        with tab_table:
            render_empty_state()
        with tab_json:
            render_empty_state()
        with tab_flow:
            render_pipeline_tab(st.session_state.active_format_key)
        with tab_about:
            render_about_tab()

    # Footer
    render_footer()


if __name__ == "__main__":
    main()
