"""
Analytics Engine - All Plotly charts and data visualizations.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st
from typing import List, Dict

# ===== SHARED THEME =====
DARK_THEME = dict(
    paper_bgcolor="rgba(13,18,38,0.0)",
    plot_bgcolor="rgba(13,18,38,0.0)",
    font_color="#ccd6f6",
    font_family="Inter, sans-serif",
)

COLORS = ["#00ff88", "#00b4d8", "#7b5ea7", "#ff6348", "#ffa502", "#2ed573", "#eccc68", "#ff4757"]
GRADIENT_COLORS = px.colors.sequential.Viridis


def _apply_dark_layout(fig, title: str = "", height: int = 350):
    """Apply shared dark theme to any Plotly figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(color="#ccd6f6", size=14, family="Inter")),
        **DARK_THEME,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            bgcolor="rgba(13,18,38,0.8)",
            bordercolor="#1e2a45",
            borderwidth=1,
            font=dict(color="#8892b0", size=11),
        ),
        xaxis=dict(
            gridcolor="#1e2a45",
            linecolor="#1e2a45",
            tickfont=dict(color="#8892b0", size=11),
            title_font=dict(color="#8892b0"),
        ),
        yaxis=dict(
            gridcolor="#1e2a45",
            linecolor="#1e2a45",
            tickfont=dict(color="#8892b0", size=11),
            title_font=dict(color="#8892b0"),
        ),
    )
    return fig


def attendance_trend_chart(data: List[Dict]) -> go.Figure:
    """Line chart of daily attendance rate over time."""
    if not data:
        return go.Figure()

    df = pd.DataFrame(data)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["rate"],
        mode="lines+markers",
        name="Attendance Rate",
        line=dict(color="#00ff88", width=2.5, shape="spline"),
        marker=dict(color="#00ff88", size=6),
        fill="tonexty",
        fillcolor="rgba(0,255,136,0.07)",
    ))

    # Add threshold line at 75%
    fig.add_hline(y=75, line_dash="dash", line_color="#ffa502",
                  annotation_text="75% Threshold", annotation_font_color="#ffa502")

    fig.update_layout(
        title="📅 Attendance Rate Trend",
        **DARK_THEME,
        height=320,
        margin=dict(l=20, r=20, t=50, b=20),
        yaxis=dict(range=[0, 105], ticksuffix="%", gridcolor="#1e2a45",
                   tickfont=dict(color="#8892b0")),
        xaxis=dict(gridcolor="#1e2a45", tickfont=dict(color="#8892b0")),
    )
    return fig


def grade_distribution_chart(marks_data: List[Dict]) -> go.Figure:
    """Bar chart of grade distribution (A+, A, B, C, D, F)."""
    if not marks_data:
        return go.Figure()

    bins = {"A+ (90-100)": 0, "A (80-89)": 0, "B (70-79)": 0,
            "C (60-69)": 0, "D (50-59)": 0, "F (<50)": 0}

    for m in marks_data:
        p = m.get("percentage") or m.get("avg_score") or 0
        if p >= 90:
            bins["A+ (90-100)"] += 1
        elif p >= 80:
            bins["A (80-89)"] += 1
        elif p >= 70:
            bins["B (70-79)"] += 1
        elif p >= 60:
            bins["C (60-69)"] += 1
        elif p >= 50:
            bins["D (50-59)"] += 1
        else:
            bins["F (<50)"] += 1

    colors_map = ["#00ff88", "#2ed573", "#00b4d8", "#ffa502", "#ff6348", "#ff4757"]
    fig = go.Figure(go.Bar(
        x=list(bins.keys()),
        y=list(bins.values()),
        marker=dict(color=colors_map, line=dict(width=0)),
        text=list(bins.values()),
        textposition="outside",
        textfont=dict(color="#ccd6f6", size=11),
    ))

    _apply_dark_layout(fig, "📊 Grade Distribution", height=320)
    fig.update_layout(showlegend=False, bargap=0.3)
    return fig


def class_comparison_chart(classes_data: List[Dict]) -> go.Figure:
    """Horizontal bar chart comparing classes by attendance rate."""
    if not classes_data:
        return go.Figure()

    df = pd.DataFrame(classes_data)
    colors = ["#00ff88" if r >= 80 else "#ffa502" if r >= 65 else "#ff4757"
              for r in df["attendance_rate"]]

    fig = go.Figure(go.Bar(
        x=df["attendance_rate"],
        y=df["class_label"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{r:.1f}%" for r in df["attendance_rate"]],
        textposition="outside",
        textfont=dict(color="#ccd6f6", size=11),
    ))

    _apply_dark_layout(fig, "🏫 Class Attendance Comparison", height=340)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(range=[0, 110], ticksuffix="%")
    return fig


def subject_performance_chart(subjects_data: List[Dict]) -> go.Figure:
    """Radar / spider chart of subject-wise performance."""
    if not subjects_data:
        return go.Figure()

    df = pd.DataFrame(subjects_data)
    subjects = df["subject_name"].tolist()
    scores = df["avg_score"].tolist()

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=subjects + [subjects[0]],
        fill="toself",
        fillcolor="rgba(0,255,136,0.12)",
        line=dict(color="#00ff88", width=2),
        marker=dict(color="#00ff88", size=7),
        name="Avg Score",
    ))

    fig.update_layout(
        title="📚 Subject Performance Radar",
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1e2a45",
                            tickfont=dict(color="#8892b0", size=10), ticksuffix="%"),
            angularaxis=dict(gridcolor="#1e2a45", tickfont=dict(color="#ccd6f6", size=11)),
            bgcolor="rgba(13,18,38,0.0)",
        ),
        **DARK_THEME,
        height=360,
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=False,
    )
    return fig


def performance_trend_chart(marks_data: List[Dict], student_name: str = "") -> go.Figure:
    """Line chart of student's performance over exams."""
    if not marks_data:
        return go.Figure()

    df = pd.DataFrame(marks_data)
    df = df.sort_values("exam_date")

    fig = go.Figure()

    if "subject_name" in df.columns:
        for i, subject in enumerate(df["subject_name"].unique()):
            sub_df = df[df["subject_name"] == subject]
            fig.add_trace(go.Scatter(
                x=sub_df["exam_date"],
                y=sub_df["percentage"],
                mode="lines+markers",
                name=subject,
                line=dict(color=COLORS[i % len(COLORS)], width=2),
                marker=dict(size=7),
            ))
    else:
        fig.add_trace(go.Scatter(
            x=df["exam_date"],
            y=df["percentage"],
            mode="lines+markers",
            line=dict(color="#00ff88", width=2),
            name="Score",
        ))

    _apply_dark_layout(fig, f"📈 Performance Trend{' - ' + student_name if student_name else ''}", 340)
    fig.update_layout(yaxis=dict(range=[0, 105], ticksuffix="%", gridcolor="#1e2a45",
                                  tickfont=dict(color="#8892b0")))
    return fig


def risk_scatter_chart(data: List[Dict]) -> go.Figure:
    """Scatter plot: attendance vs average score (risk visualization)."""
    if not data:
        return go.Figure()

    df = pd.DataFrame(data)
    df = df.dropna(subset=["avg_score", "attendance_rate"])

    def get_risk_color(row):
        if row["avg_score"] < 50 or row["attendance_rate"] < 65:
            return "#ff4757"
        elif row["avg_score"] < 65 or row["attendance_rate"] < 75:
            return "#ffa502"
        else:
            return "#00ff88"

    df["color"] = df.apply(get_risk_color, axis=1)

    fig = go.Figure()

    # Zone rectangles
    fig.add_shape(type="rect", x0=0, y0=0, x1=65, y1=100,
                  fillcolor="rgba(255,71,87,0.05)", line=dict(width=0))
    fig.add_shape(type="rect", x0=65, y0=0, x1=80, y1=100,
                  fillcolor="rgba(255,165,2,0.05)", line=dict(width=0))

    fig.add_trace(go.Scatter(
        x=df["attendance_rate"],
        y=df["avg_score"],
        mode="markers",
        marker=dict(
            color=df["color"],
            size=10,
            opacity=0.85,
            line=dict(width=1, color="#0a0e1a"),
        ),
        text=df["full_name"] if "full_name" in df.columns else None,
        hovertemplate="<b>%{text}</b><br>Attendance: %{x:.1f}%<br>Score: %{y:.1f}%<extra></extra>",
    ))

    # Quadrant lines
    fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,71,87,0.4)")
    fig.add_vline(x=75, line_dash="dash", line_color="rgba(255,165,2,0.4)")

    _apply_dark_layout(fig, "🎯 Risk Analysis: Attendance vs Performance", 380)
    fig.update_xaxes(title_text="Attendance Rate (%)", ticksuffix="%")
    fig.update_yaxes(title_text="Average Score (%)", ticksuffix="%")
    return fig


def fee_collection_chart(fee_data: Dict) -> go.Figure:
    """Donut chart for fee collection status."""
    labels = ["Paid", "Unpaid", "Partial"]
    values = [
        fee_data.get("paid_count") or 0,
        fee_data.get("unpaid_count") or 0,
        fee_data.get("partial_count") or 0,
    ]
    colors_pie = ["#00ff88", "#ff4757", "#ffa502"]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors_pie, line=dict(color="#0a0e1a", width=2)),
        textfont=dict(color="#ccd6f6", size=12),
        textinfo="percent+label",
    ))

    fig.update_layout(
        title="💰 Fee Collection Status",
        **DARK_THEME,
        height=300,
        margin=dict(l=10, r=10, t=50, b=10),
        annotations=[dict(text="Fees", x=0.5, y=0.5, font_size=16,
                          font_color="#ccd6f6", showarrow=False)],
        showlegend=True,
    )
    return fig


def heatmap_attendance(data: List[Dict]) -> go.Figure:
    """Heatmap of class attendance rates by class."""
    if not data:
        return go.Figure()

    df = pd.DataFrame(data)
    fig = go.Figure(go.Bar(
        x=df["class_label"],
        y=df["attendance_rate"],
            marker=dict(
            color=df["attendance_rate"],
            colorscale=[[0, "#ff4757"], [0.5, "#ffa502"], [1, "#00ff88"]],
            cmin=50, cmax=100,
            showscale=True,
            colorbar=dict(
                title=dict(text="Rate %", font=dict(color="#8892b0")),
                tickfont=dict(color="#8892b0"),
            ),
        ),
        text=[f"{r:.1f}%" for r in df["attendance_rate"]],
        textposition="outside",
        textfont=dict(color="#ccd6f6"),
    ))

    _apply_dark_layout(fig, "🔥 Attendance Heatmap by Class", 320)
    fig.update_layout(showlegend=False)
    fig.update_yaxes(ticksuffix="%", range=[0, 110])
    return fig


def student_marks_bar(marks_data: List[Dict], student_name: str = "") -> go.Figure:
    """Bar chart of student marks by subject."""
    if not marks_data:
        return go.Figure()

    df = pd.DataFrame(marks_data)
    if "subject_name" not in df.columns:
        return go.Figure()

    # Average by subject
    avg = df.groupby("subject_name")["percentage"].mean().reset_index()

    bar_colors = ["#00ff88" if s >= 70 else "#ffa502" if s >= 50 else "#ff4757"
                  for s in avg["percentage"]]

    fig = go.Figure(go.Bar(
        x=avg["subject_name"],
        y=avg["percentage"],
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{s:.1f}%" for s in avg["percentage"]],
        textposition="outside",
        textfont=dict(color="#ccd6f6", size=11),
    ))

    _apply_dark_layout(fig, f"📝 Marks by Subject - {student_name}", 300)
    fig.update_layout(showlegend=False, bargap=0.35)
    fig.update_yaxes(range=[0, 110], ticksuffix="%")
    return fig


def dropout_risk_gauge(risk_score: float) -> go.Figure:
    """Gauge chart for dropout risk."""
    color = "#00ff88" if risk_score < 30 else "#ffa502" if risk_score < 60 else "#ff4757"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Dropout Risk Score", "font": {"color": "#ccd6f6", "size": 13}},
        number={"suffix": "%", "font": {"color": color, "size": 32}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#8892b0",
                     "tickfont": {"color": "#8892b0"}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#111827",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 30], "color": "rgba(46,213,115,0.1)"},
                {"range": [30, 60], "color": "rgba(255,165,2,0.1)"},
                {"range": [60, 100], "color": "rgba(255,71,87,0.1)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.75,
                "value": risk_score,
            },
        },
    ))

    fig.update_layout(**DARK_THEME, height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig
