"""
AI Alert System - Intelligent alert generation based on school data analysis.
"""

import logging
import streamlit as st
from datetime import datetime
from src.database.db_manager import DatabaseManager
from src.components.ui_components import alert_card, section_header

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Generates and manages intelligent AI alerts based on school performance data.
    Alert types: attendance_drop, low_performance, fee_overdue, dropout_risk, class_decline.
    """

    THRESHOLDS = {
        "critical_attendance": 60,
        "low_attendance": 75,
        "critical_score": 40,
        "low_score": 55,
        "critical_fee_days": 60,
    }

    def __init__(self, school_id: int = 1):
        self.school_id = school_id
        self.db = DatabaseManager()

    def generate_alerts(self) -> list:
        """
        Analyze school data and generate intelligent AI alerts.
        Returns a list of new alert dicts (does not save to DB).
        """
        alerts = []

        try:
            students = self.db.get_all_students(self.school_id)
            alerts += self._check_student_attendance_alerts(students)
            alerts += self._check_student_performance_alerts(students)
            alerts += self._check_class_performance_alerts()
            alerts += self._check_fee_alerts(students)
        except Exception as e:
            logger.error(f"Alert generation error: {e}")

        return alerts

    def _check_student_attendance_alerts(self, students: list) -> list:
        alerts = []
        for student in students:
            sid = student["student_id"]
            att_rate = self.db.get_attendance_rate(sid, days=30)
            student_name = student["full_name"]
            class_label = f"{student.get('class_name', '')} {student.get('section', '')}".strip()

            if att_rate < self.THRESHOLDS["critical_attendance"]:
                alerts.append({
                    "type": "attendance_drop",
                    "severity": "critical",
                    "title": f"Critical Attendance: {student_name}",
                    "message": f"{student_name} attendance is {att_rate:.1f}% this month — below critical threshold of {self.THRESHOLDS['critical_attendance']}%. Immediate parent contact and intervention required.",
                    "student_id": sid,
                    "class_label": class_label,
                    "data": {"attendance_rate": att_rate},
                })
            elif att_rate < self.THRESHOLDS["low_attendance"]:
                alerts.append({
                    "type": "attendance_warning",
                    "severity": "medium",
                    "title": f"Attendance Warning: {student_name}",
                    "message": f"{student_name} attendance is {att_rate:.1f}% — below the recommended 75%. Parent notification is advised.",
                    "student_id": sid,
                    "class_label": class_label,
                    "data": {"attendance_rate": att_rate},
                })

        return alerts

    def _check_student_performance_alerts(self, students: list) -> list:
        alerts = []
        for student in students:
            sid = student["student_id"]
            marks = self.db.get_student_marks(sid)
            if not marks:
                continue

            avg_score = sum(m["percentage"] for m in marks) / len(marks)
            student_name = student["full_name"]
            class_label = f"{student.get('class_name', '')} {student.get('section', '')}".strip()

            if avg_score < self.THRESHOLDS["critical_score"]:
                alerts.append({
                    "type": "low_performance",
                    "severity": "high",
                    "title": f"Academic Alert: {student_name}",
                    "message": f"{student_name} has an average score of {avg_score:.1f}% — at high risk of failure. Immediate academic support required.",
                    "student_id": sid,
                    "class_label": class_label,
                    "data": {"avg_score": avg_score},
                })
            elif avg_score < self.THRESHOLDS["low_score"]:
                alerts.append({
                    "type": "performance_warning",
                    "severity": "medium",
                    "title": f"Performance Concern: {student_name}",
                    "message": f"{student_name} scores {avg_score:.1f}% average. Additional tutoring and study support recommended.",
                    "student_id": sid,
                    "class_label": class_label,
                    "data": {"avg_score": avg_score},
                })

        return alerts

    def _check_class_performance_alerts(self) -> list:
        alerts = []
        classes = self.db.get_all_classes(self.school_id)
        att_summary = self.db.get_class_attendance_summary(self.school_id, days=30)
        att_by_class = {r["class_label"]: r["attendance_rate"] for r in att_summary}

        for cls in classes:
            class_label = f"{cls['class_name']} {cls['section']}"
            att = att_by_class.get(class_label, 100)

            if att < 65:
                alerts.append({
                    "type": "class_attendance",
                    "severity": "high",
                    "title": f"Class Attendance Critical: {class_label}",
                    "message": f"{class_label} class attendance is {att:.1f}% — significantly below expected levels. Review class schedule, teacher, and student engagement.",
                    "student_id": None,
                    "class_label": class_label,
                    "data": {"attendance_rate": att},
                })

        return alerts

    def _check_fee_alerts(self, students: list) -> list:
        alerts = []
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT f.*, s.full_name, s.student_id
                    FROM fees f
                    JOIN students s ON f.student_id = s.student_id
                    WHERE s.school_id = ? AND f.status = 'unpaid'
                    AND f.due_date < date('now')
                """, (self.school_id,))
                overdue_fees = [dict(r) for r in cursor.fetchall()]

            for fee in overdue_fees[:5]:  # Limit to top 5
                alerts.append({
                    "type": "fee_overdue",
                    "severity": "medium",
                    "title": f"Fee Overdue: {fee['full_name']}",
                    "message": f"{fee['full_name']}'s {fee['fee_type']} fee of ${fee['amount']:.0f} is overdue. Contact parent to arrange payment.",
                    "student_id": fee["student_id"],
                    "class_label": "",
                    "data": {"amount": fee["amount"], "fee_type": fee["fee_type"]},
                })
        except Exception as e:
            logger.error(f"Fee alert check error: {e}")

        return alerts

    def get_recommendations(self, stats: dict) -> list:
        """Generate school-wide AI recommendations based on overall statistics."""
        recommendations = []

        att_rate = stats.get("attendance_rate", 80)
        avg_marks = stats.get("avg_marks", 60)

        if att_rate < 75:
            recommendations.append({
                "icon": "📅",
                "title": "Improve Attendance Strategy",
                "desc": "School-wide attendance is below 75%. Launch an attendance incentive program and automated SMS alerts for parents.",
                "priority": "high",
            })

        if avg_marks < 60:
            recommendations.append({
                "icon": "📚",
                "title": "Academic Support Program",
                "desc": "Average marks below 60%. Introduce peer tutoring, extra revision sessions, and subject-specific remediation classes.",
                "priority": "high",
            })

        recommendations.append({
            "icon": "👨‍👩‍👧",
            "title": "Parent Engagement Initiative",
            "desc": "Research shows 3x better outcomes when parents receive weekly progress reports. Enable automated weekly summaries.",
            "priority": "medium",
        })

        recommendations.append({
            "icon": "🧠",
            "title": "Personalized Learning Paths",
            "desc": "Use AI prediction data to create individual improvement plans for the bottom 20% of students.",
            "priority": "medium",
        })

        recommendations.append({
            "icon": "⏰",
            "title": "Study Hours Correlation",
            "desc": "Students studying 4+ hours daily score 28% higher on average. Promote structured home study schedules.",
            "priority": "low",
        })

        return recommendations


def render_alerts_page(school_id: int = 1):
    """Full alerts page with live generation and resolution."""
    section_header("AI Alerts", "Intelligent alerts generated from real-time school data analysis", "🔔")

    db = DatabaseManager()
    engine = AlertEngine(school_id)

    tab1, tab2, tab3 = st.tabs(["🚨 Active Alerts", "⚙️ Generate New Alerts", "✅ Resolved Alerts"])

    with tab1:
        active_alerts = db.get_ai_alerts(school_id, resolved=False)

        if not active_alerts:
            st.info("✅ No active alerts. Your school is performing well!")
        else:
            st.markdown(f"**{len(active_alerts)} active alerts require attention**")

            for alert in active_alerts:
                col1, col2 = st.columns([5, 1])
                with col1:
                    from src.utils.helpers import time_ago
                    alert_card(
                        title=alert["title"],
                        message=alert["message"],
                        severity=alert["severity"],
                        student=alert.get("student_name", ""),
                        time_str=time_ago(alert["created_at"]) if alert.get("created_at") else "",
                    )
                with col2:
                    st.markdown("<div style='padding-top:12px;'></div>", unsafe_allow_html=True)
                    if st.button("✅ Resolve", key=f"resolve_{alert['alert_id']}", use_container_width=True):
                        db.resolve_alert(alert["alert_id"])
                        st.success("Alert resolved!")
                        st.rerun()

    with tab2:
        st.markdown("**Generate fresh alerts based on current school data:**")
        if st.button("🔍 Run AI Alert Scan", use_container_width=True, type="primary"):
            with st.spinner("Analyzing school data for new alerts..."):
                new_alerts = engine.generate_alerts()

            if new_alerts:
                st.success(f"Found {len(new_alerts)} new alerts!")
                for alert in new_alerts:
                    alert_card(
                        title=alert["title"],
                        message=alert["message"],
                        severity=alert["severity"],
                        student=f"Class: {alert.get('class_label', '')}" if alert.get("class_label") else "",
                    )
                if st.button("💾 Save These Alerts to Database", use_container_width=True):
                    for alert in new_alerts:
                        try:
                            db.add_ai_alert(
                                school_id=school_id,
                                student_id=alert.get("student_id"),
                                class_id=None,
                                alert_type=alert["type"],
                                severity=alert["severity"],
                                title=alert["title"],
                                message=alert["message"],
                            )
                        except Exception as e:
                            logger.error(f"Failed to save alert: {e}")
                    st.success("Alerts saved!")
                    st.rerun()
            else:
                st.success("✅ No new alerts generated. School performance looks good!")

        # Recommendations
        st.markdown("---")
        section_header("AI Recommendations", "", "💡")
        stats = db.get_school_summary(school_id)
        recs = engine.get_recommendations(stats)

        for rec in recs:
            priority_colors = {"high": "#ff4757", "medium": "#ffa502", "low": "#00ff88"}
            color = priority_colors.get(rec["priority"], "#ccd6f6")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg,#0d1226,#111827); border:1px solid #1e2a45;
                        border-left: 4px solid {color}; border-radius: 12px; padding: 16px 20px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                    <span style="font-size:1.3rem;">{rec['icon']}</span>
                    <strong style="color:#ccd6f6;">{rec['title']}</strong>
                    <span style="margin-left:auto; background:{color}20; color:{color};
                                 border-radius:6px; padding:2px 8px; font-size:0.75rem; font-weight:600;">
                        {rec['priority'].upper()}
                    </span>
                </div>
                <p style="color:#8892b0; font-size:0.85rem; margin:0;">{rec['desc']}</p>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        resolved_alerts = db.get_ai_alerts(school_id, resolved=True)
        if not resolved_alerts:
            st.info("No resolved alerts yet.")
        else:
            st.markdown(f"**{len(resolved_alerts)} resolved alerts**")
            for alert in resolved_alerts:
                alert_card(
                    title=f"✅ {alert['title']}",
                    message=alert["message"],
                    severity="low",
                )
