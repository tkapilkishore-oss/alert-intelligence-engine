"""Custom CSS styling for Alert Intelligence Engine Streamlit Dashboard."""

MAIN_CSS = """
<style>
/* Main Container Spacing */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2.5rem;
    max-width: 95%;
}

/* Typography & Base Adjustments */
h1, h2, h3, h4 {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-weight: 600;
}

/* Metric Cards */
.kpi-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.kpi-card:hover {
    border-color: rgba(0, 198, 255, 0.4);
    transform: translateY(-2px);
}
.kpi-title {
    font-size: 0.825rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94A3B8;
    margin-bottom: 6px;
    font-weight: 600;
}
.kpi-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1.2;
}
.kpi-subtext {
    font-size: 0.75rem;
    color: #64748B;
    margin-top: 4px;
}

/* Hero Section */
.hero-container {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 24px 30px;
    margin-bottom: 24px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}
.hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    color: #F8FAFC;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: #94A3B8;
    margin-bottom: 16px;
}
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background-color: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.badge-extreme { background-color: rgba(239, 68, 68, 0.2); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.4); }
.badge-severe  { background-color: rgba(249, 115, 22, 0.2); color: #FDBA74; border: 1px solid rgba(249, 115, 22, 0.4); }
.badge-moderate{ background-color: rgba(234, 179, 8, 0.2); color: #FDE047; border: 1px solid rgba(234, 179, 8, 0.4); }
.badge-minor   { background-color: rgba(34, 197, 94, 0.2); color: #86EFAC; border: 1px solid rgba(34, 197, 94, 0.4); }
.badge-unknown { background-color: rgba(148, 163, 184, 0.2); color: #CBD5E1; border: 1px solid rgba(148, 163, 184, 0.4); }

.badge-duplicate { background-color: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.badge-canonical { background-color: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.3); }

.badge-format {
    background-color: rgba(168, 85, 247, 0.15);
    color: #C084FC;
    border: 1px solid rgba(168, 85, 247, 0.3);
}

/* Alert Detail Cards */
.alert-card-wrapper {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}
.alert-property-label {
    font-size: 0.75rem;
    color: #94A3B8;
    text-transform: uppercase;
    font-weight: 600;
}
.alert-property-value {
    font-size: 0.95rem;
    color: #F1F5F9;
    font-weight: 500;
}

/* Pipeline Flow Boxes */
.pipeline-step-box {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: center;
    margin-bottom: 8px;
}
.pipeline-step-box.active-format {
    border-color: #38BDF8;
    background: rgba(56, 189, 248, 0.1);
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
}

/* Error Panel */
.error-panel {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 8px;
    padding: 16px 20px;
    margin: 16px 0;
    color: #FCA5A5;
}

/* Landing Page / Empty State */
.landing-card {
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 32px;
    margin-top: 16px;
}

/* Footer */
.dashboard-footer {
    border-top: 1px solid #334155;
    padding-top: 16px;
    margin-top: 40px;
    text-align: center;
    color: #64748B;
    font-size: 0.8rem;
}
</style>
"""


def get_severity_badge_html(severity: str) -> str:
    """Return HTML badge string for alert severity.

    Args:
        severity: Normalized severity string.

    Returns:
        str: Styled HTML badge span.
    """
    sev_lower = (severity or "unknown").lower()
    badge_class = f"badge-{sev_lower}" if sev_lower in ["extreme", "severe", "moderate", "minor"] else "badge-unknown"
    return f'<span class="badge {badge_class}">{severity}</span>'


def get_duplicate_badge_html(is_duplicate: bool) -> str:
    """Return HTML badge string for duplicate status.

    Args:
        is_duplicate: Boolean duplicate flag.

    Returns:
        str: Styled HTML badge span.
    """
    if is_duplicate:
        return '<span class="badge badge-duplicate">DUPLICATE</span>'
    return '<span class="badge badge-canonical">CANONICAL</span>'
