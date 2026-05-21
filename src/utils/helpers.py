"""
Utility helpers used across the application.
"""

import streamlit as st
from datetime import datetime


def grade_from_score(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "F"


def risk_level(score: float, attendance: float) -> str:
    """Compute dropout risk level from score and attendance."""
    risk_score = 0
    if score < 40:
        risk_score += 3
    elif score < 55:
        risk_score += 2
    elif score < 65:
        risk_score += 1

    if attendance < 60:
        risk_score += 3
    elif attendance < 75:
        risk_score += 2
    elif attendance < 85:
        risk_score += 1

    if risk_score >= 5:
        return "🔴 Critical"
    elif risk_score >= 3:
        return "🟠 High"
    elif risk_score >= 1:
        return "🟡 Medium"
    else:
        return "🟢 Low"


def risk_color(level: str) -> str:
    """Return color string for risk level."""
    mapping = {
        "🔴 Critical": "#ff4757",
        "🟠 High": "#ff6348",
        "🟡 Medium": "#ffa502",
        "🟢 Low": "#2ed573",
    }
    return mapping.get(level, "#ccd6f6")


def format_percentage(value: float) -> str:
    """Format a float as percentage string."""
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


def format_currency(value: float) -> str:
    """Format a float as currency string."""
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"


def severity_emoji(severity: str) -> str:
    """Get emoji for alert severity."""
    mapping = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }
    return mapping.get(severity.lower(), "⚪")


def time_ago(dt_str: str) -> str:
    """Convert a datetime string to 'X ago' format."""
    try:
        dt = datetime.strptime(dt_str[:19], "%Y-%m-%d %H:%M:%S")
        delta = datetime.now() - dt
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        mins = delta.seconds // 60
        return f"{mins}m ago"
    except Exception:
        return dt_str


def paginate_dataframe(df, page_size: int = 10, key: str = "page"):
    """Paginate a dataframe with previous/next controls."""
    import math
    total_pages = max(1, math.ceil(len(df) / page_size))
    if f"df_page_{key}" not in st.session_state:
        st.session_state[f"df_page_{key}"] = 1

    page = st.session_state[f"df_page_{key}"]
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀ Prev", key=f"prev_{key}", disabled=(page <= 1)):
            st.session_state[f"df_page_{key}"] -= 1
            st.rerun()
    with col2:
        st.markdown(f"<p style='text-align:center;color:#8892b0;'>Page {page} of {total_pages}</p>",
                    unsafe_allow_html=True)
    with col3:
        if st.button("Next ▶", key=f"next_{key}", disabled=(page >= total_pages)):
            st.session_state[f"df_page_{key}"] += 1
            st.rerun()

    return page_df
