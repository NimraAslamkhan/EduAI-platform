"""
Parent Dashboard - Child performance monitoring, attendance, and AI insights.
"""

import streamlit as st
import pandas as pd
from src.database.db_manager import DatabaseManager
from src.components.ui_components import (
    kpi_card, section_header, page_header, render_sidebar_nav, alert_card
)
from src.analytics.analytics_engine import (
    student_marks_bar, performance_trend_chart, attendance_trend_chart, dropout_risk_gauge
)
from src.utils.helpers import grade_from_score, risk_level, time_ago


def render_parent_dashboard():
    """Render the Parent dashboard."""
    user = st.session_state.user
    db = DatabaseManager()

    nav_items = [
        {"label": "🏠 Dashboard", "page": "Dashboard"},
        {"label": "📊 Child Performance", "page": "Performance"},
        {"label": "📅 Attendance", "page": "Attendance"},
        {"label": "🔔 Notifications", "page": "Notifications"},
        {"label": "🤖 AI Assistant", "page": "AI Assistant"},
        {"label": "⚙️ Settings", "page": "Settings"},
    ]

    render_sidebar_nav(
        nav_items,
        role_label="Parent",
        user_name=user["full_name"],
        school_name=user.get("school_name", ""),
    )

    page = st.session_state.get("page", "Dashboard")

    # Get parent's children
    # Allow parent to link a child by student_id + school_id
    with st.expander("🔗 Link a child to your account (enter Student ID and School ID)", expanded=False):
        sid = st.text_input("Student ID (numeric)")
        sch = st.text_input("School ID (numeric)")
        if st.button("Link Child"):
            try:
                sid_i = int(sid)
                sch_i = int(sch)
                st.info("Verifying student...")
                srec = db.get_student_by_id(sid_i)
                if not srec:
                    st.error("No student found with that ID.")
                elif srec.get('school_id') != sch_i:
                    st.error("Student does not belong to the provided school ID.")
                else:
                    db.assign_parent_to_student(sid_i, user['user_id'])
                    st.success(f"Linked {srec.get('full_name')} (ID: {sid_i}) to your account.")
                    st.experimental_rerun()
            except ValueError:
                st.error("Please enter valid numeric IDs.")

    children = db.get_students_by_parent(user["user_id"])
    if not children:
        # Fallback: show first few students for demo
        all_students = db.get_all_students(school_id=user.get('school_id', 1))
        children = all_students[:2] if all_students else []

    if page == "Dashboard":
        _render_parent_overview(db, user, children)
    elif page == "Performance":
        _render_child_performance(db, children)
    elif page == "Attendance":
        _render_child_attendance(db, children)
    elif page == "Notifications":
        _render_notifications(db)
    elif page == "AI Assistant":
        _render_ai_assistant(db, user)
    elif page == "Settings":
        _render_settings(db, user)


def _render_parent_overview(db: DatabaseManager, user: dict, children: list):
    page_header(f"Welcome, {user['full_name'].split('(')[0].strip()}", "Monitor your child's progress", "👨‍👩‍👧")

    if not children:
        st.warning("No children linked to your account. Please contact the school administrator.")
        return

    # Child selector if multiple children
    if len(children) > 1:
        child_map = {c["student_id"]: c["full_name"] for c in children}
        selected_id = st.selectbox("Select Child", options=list(child_map.keys()),
                                    format_func=lambda x: child_map[x])
        child = next(c for c in children if c["student_id"] == selected_id)
    else:
        child = children[0]

    student_id = child["student_id"]
    marks = db.get_student_marks(student_id)
    att_rate = db.get_attendance_rate(student_id, 30)
    avg_score = round(sum(m["percentage"] for m in marks) / len(marks), 1) if marks else 0

    # Child header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0d1226, #111827); border:1px solid #1e2a45;
                border-radius:16px; padding:24px; margin-bottom:24px;">
        <div style="display:flex; align-items:center; gap:20px;">
            <div style="background: linear-gradient(135deg,#00ff88,#00b4d8); border-radius:50%;
                        width:60px; height:60px; display:flex; align-items:center;
                        justify-content:center; font-size:1.8rem;">👧</div>
            <div>
                <h2 style="color:#ccd6f6; margin:0 0 4px 0; font-size:1.5rem;">{child['full_name']}</h2>
                <p style="color:#8892b0; margin:0;">
                    📚 {child.get('class_name', 'N/A')} {child.get('section', '')} •
                    🎂 Age {child.get('age', 'N/A')} •
                    ⏰ Studies {child.get('study_hours', 'N/A')}h/day
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Overall Grade", grade_from_score(avg_score), f"Avg: {avg_score}%", "🎓",
                 "#00ff88" if avg_score >= 65 else "#ff6348")
    with c2:
        kpi_card("Average Score", f"{avg_score}%", "All subjects", "📊",
                 "#00ff88" if avg_score >= 65 else "#ffa502")
    with c3:
        kpi_card("Attendance", f"{att_rate}%", "Last 30 days", "📅",
                 "#00ff88" if att_rate >= 80 else "#ff4757")
    with c4:
        rl = risk_level(avg_score, att_rate)
        risk_colors = {"🔴 Critical": "#ff4757", "🟠 High": "#ff6348",
                       "🟡 Medium": "#ffa502", "🟢 Low": "#00ff88"}
        kpi_card("Risk Level", rl.split()[-1], "Academic risk", "⚠️",
                 risk_colors.get(rl, "#00ff88"))

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        section_header("Subject Performance", "", "📚")
        if marks:
            st.plotly_chart(student_marks_bar(marks, child["full_name"]), use_container_width=True)
            st.plotly_chart(performance_trend_chart(marks, child["full_name"]), use_container_width=True)
        else:
            st.info("No marks recorded yet.")

    with col_right:
        section_header("Dropout Risk Assessment", "", "🎯")
        risk_score_val = (100 - avg_score) * 0.5 + (100 - att_rate) * 0.5
        risk_score_val = max(0, min(100, risk_score_val))
        st.plotly_chart(dropout_risk_gauge(risk_score_val), use_container_width=True)

        section_header("AI Insights", "", "🤖")
        rl = risk_level(avg_score, att_rate)
        if rl in ("🔴 Critical", "🟠 High"):
            st.error(f"""
            **Immediate Action Required** ⚠️
            
            {child['full_name']} is showing signs of academic struggle:
            - Average score: {avg_score}%
            - Attendance: {att_rate}%
            
            **Please contact the school immediately.**
            """)
        elif rl == "🟡 Medium":
            st.warning(f"""
            **Needs Improvement** 📈
            
            {child['full_name']} can do better with some extra support:
            - Encourage daily study routine (target 4+ hours)
            - Review missed lessons together
            - Contact teacher for weak subjects
            """)
        else:
            st.success(f"""
            **Performing Well** ✅
            
            {child['full_name']} is on a great track!
            - Keep encouraging the study routine
            - Celebrate academic achievements
            - Focus on maintaining attendance above 85%
            """)

    # Fees & Assignments
    st.markdown("---")
    section_header("Fees & Assignments", "Billing status and outstanding homework", "💼")
    student_id = child["student_id"]

    # Fees
    fees = db.get_fees_for_student(student_id)
    if fees:
        df_fees = pd.DataFrame(fees)[["fee_id","fee_type","amount","paid_amount","due_date","status"]]
        st.markdown("**Fee Records**")
        st.dataframe(df_fees, use_container_width=True, height=180)
        total_due = sum((f.get('amount') or 0) - (f.get('paid_amount') or 0) for f in fees)
        if total_due > 0:
            st.warning(f"Outstanding balance: {total_due}")
        else:
            st.success("All fees are paid up-to-date.")
    else:
        st.info("No fee records found for this child.")

    # Assignments
    assignments = db.get_assignments_for_student(student_id)
    if assignments:
        df_asg = pd.DataFrame(assignments)[["assignment_id","title","description","due_date","status","subject_name"]]
        st.markdown("**Assignments (by class)**")
        st.dataframe(df_asg, use_container_width=True, height=180)
    else:
        st.info("No open assignments for this child.")

    # Notifications for this parent (school-level)
    st.markdown("---")
    section_header("Notifications", "School announcements relevant to parents", "🔔")
    school_id = user.get('school_id', 1)
    notifs = db.get_notifications_for_role(school_id=school_id, role='parent', limit=10)
    if notifs:
        for notif in notifs:
            st.markdown(f"**{notif['title']}** — {notif.get('type','info').upper()}")
            st.write(notif['message'])
    else:
        st.info("No notifications at this time.")

    # AI Parenting Suggestions
    st.markdown("---")
    section_header("AI Parenting Suggestions", "Personalized guidance and improvement recommendations", "🤖")
    from src.chatbot.groq_chatbot import render_chatbot_ui
    child_stats = {
        "full_name": child.get('full_name'),
        "avg_score": avg_score,
        "attendance": att_rate,
        "study_hours": child.get('study_hours')
    }
    render_chatbot_ui(context={"school_info": {"school_name": user.get('school_name','')}, "stats": child_stats})


def _render_child_performance(db: DatabaseManager, children: list):
    page_header("Child Performance", "Detailed academic performance analysis", "📊")

    if not children:
        st.info("No children found.")
        return

    if len(children) > 1:
        child_map = {c["student_id"]: c["full_name"] for c in children}
        selected_id = st.selectbox("Select Child", list(child_map.keys()),
                                    format_func=lambda x: child_map[x])
        child = next(c for c in children if c["student_id"] == selected_id)
    else:
        child = children[0]

    student_id = child["student_id"]
    marks = db.get_student_marks(student_id)

    if not marks:
        st.info("No marks recorded yet. Check back after the first examination.")
        return

    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Detailed Marks", "📈 Trends"])

    with tab1:
        avg = round(sum(m["percentage"] for m in marks) / len(marks), 1)

        col1, col2, col3 = st.columns(3)
        with col1:
            kpi_card("Overall Average", f"{avg}%", "All subjects & exams", "📊",
                     "#00ff88" if avg >= 65 else "#ffa502")
        with col2:
            kpi_card("Overall Grade", grade_from_score(avg), "Letter grade", "🎓",
                     "#00ff88" if avg >= 65 else "#ff6348")
        with col3:
            best_subject = max(
                set(m["subject_name"] for m in marks),
                key=lambda s: sum(m["percentage"] for m in marks if m["subject_name"] == s) /
                              sum(1 for m in marks if m["subject_name"] == s)
            ) if marks else "N/A"
            kpi_card("Best Subject", best_subject[:15], "Highest average", "⭐", "#00b4d8")

        st.plotly_chart(student_marks_bar(marks, child["full_name"]), use_container_width=True)

        # Subject-wise breakdown
        section_header("Subject Analysis", "", "📚")
        subjects_data = {}
        for m in marks:
            subj = m["subject_name"]
            if subj not in subjects_data:
                subjects_data[subj] = []
            subjects_data[subj].append(m["percentage"])

        for subj, scores in subjects_data.items():
            avg_subj = round(sum(scores) / len(scores), 1)
            grade = grade_from_score(avg_subj)
            bar_width = min(100, avg_subj)
            color = "#00ff88" if avg_subj >= 70 else "#ffa502" if avg_subj >= 50 else "#ff4757"
            st.markdown(f"""
            <div style="margin-bottom: 12px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="color:#ccd6f6; font-size:0.9rem; font-weight:600;">{subj}</span>
                    <span style="color:{color}; font-weight:700;">{avg_subj}% ({grade})</span>
                </div>
                <div style="background:#1e2a45; border-radius:8px; height:8px; overflow:hidden;">
                    <div style="background:{color}; width:{bar_width}%; height:100%; border-radius:8px;
                                transition: width 0.3s ease;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        df = pd.DataFrame(marks)
        display_df = df[["subject_name", "exam_type", "marks_obtained", "total_marks",
                          "percentage", "exam_date"]].rename(columns={
            "subject_name": "Subject", "exam_type": "Exam Type",
            "marks_obtained": "Score", "total_marks": "Total",
            "percentage": "Percentage", "exam_date": "Date"
        })
        display_df["Grade"] = display_df["Percentage"].apply(grade_from_score)
        st.dataframe(display_df, use_container_width=True, height=400)

    with tab3:
        st.plotly_chart(performance_trend_chart(marks, child["full_name"]), use_container_width=True)


def _render_child_attendance(db: DatabaseManager, children: list):
    page_header("Attendance Record", "Your child's attendance history", "📅")

    if not children:
        return

    if len(children) > 1:
        child_map = {c["student_id"]: c["full_name"] for c in children}
        selected_id = st.selectbox("Select Child", list(child_map.keys()),
                                    format_func=lambda x: child_map[x])
        child = next(c for c in children if c["student_id"] == selected_id)
    else:
        child = children[0]

    student_id = child["student_id"]

    col1, col2 = st.columns([1, 2])
    with col1:
        period = st.selectbox("Period", ["Last 30 days", "Last 60 days"])
    days = 30 if "30" in period else 60

    att_records = db.get_student_attendance(student_id, days=days)
    att_rate = db.get_attendance_rate(student_id, days=days)

    # KPIs
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Attendance Rate", f"{att_rate}%", f"Last {days} days", "📅",
                 "#00ff88" if att_rate >= 80 else "#ff4757")
    with c2:
        present = sum(1 for r in att_records if r["status"] == "present")
        kpi_card("Present Days", str(present), "Out of total school days", "✅", "#00ff88")
    with c3:
        absent = sum(1 for r in att_records if r["status"] == "absent")
        kpi_card("Absent Days", str(absent), "Total absences", "❌",
                 "#ff4757" if absent > 5 else "#ffa502")

    # Trend chart
    trend_data = db.get_attendance_trend(school_id=1, days=days)
    st.plotly_chart(attendance_trend_chart(trend_data), use_container_width=True)

    # Calendar-style attendance
    section_header("Attendance Log", f"Last {days} days", "📋")
    if att_records:
        df = pd.DataFrame(att_records)
        status_map = {"present": "✅ Present", "absent": "❌ Absent", "late": "🕐 Late"}
        df["Status"] = df["status"].map(status_map)
        display_df = df[["date", "Status"]].rename(columns={"date": "Date"})
        st.dataframe(display_df, use_container_width=True, height=350)

    # Warning if attendance is low
    if att_rate < 75:
        st.error(f"""
        ⚠️ **Attendance Warning**
        
        {child['full_name']}'s attendance is {att_rate:.1f}%, which is below the minimum requirement of 75%.
        
        Please ensure your child attends school regularly. Students with low attendance are at higher academic risk.
        Contact the school if there are any ongoing issues.
        """)


def _render_notifications(db: DatabaseManager):
    page_header("Notifications", "School updates and alerts for your child", "🔔")

    user = st.session_state.user
    school_id = user.get('school_id', 1)
    notifs = db.get_notifications_for_role(school_id=school_id, role='parent', limit=20)

    if not notifs:
        st.info("No notifications at the moment.")
        return

    type_icons = {"info": "ℹ️", "warning": "⚠️", "alert": "🔔", "success": "✅"}

    for notif in notifs:
        icon = type_icons.get(notif.get("type", "info"), "ℹ️")
        sev = "medium" if notif.get("type") == "warning" else \
              "high" if notif.get("type") == "alert" else "low"
        alert_card(
            title=f"{icon} {notif['title']}",
            message=notif["message"],
            severity=sev,
            time_str=time_ago(notif["created_at"]) if notif.get("created_at") else "",
        )


def _render_ai_assistant(db: DatabaseManager, user: dict):
    stats = db.get_school_summary(school_id=1)
    context = {
        "school_info": {"school_name": user.get("school_name", "")},
        "stats": stats,
    }
    from src.chatbot.groq_chatbot import render_chatbot_ui
    render_chatbot_ui(context)


def _render_settings(db: DatabaseManager, user: dict):
    """Parent settings: child tracking and notification preferences."""
    page_header("Settings", "Parent account and child-tracking preferences", "⚙️")

    with st.form("parent_settings_form"):
        st.markdown("**Child Tracking Preferences**")
        show_assignments = st.checkbox("Show assignments & homework alerts", value=True)
        show_fees = st.checkbox("Show fee reminders", value=True)
        ai_summaries = st.checkbox("Receive weekly AI summaries about my child", value=True)

        st.markdown("**Notifications**")
        email_notif = st.checkbox("Email notifications for new alerts", value=True)
        sms_notif = st.checkbox("SMS notifications (requires phone)", value=False)

        if st.form_submit_button("Save Settings"):
            st.session_state.parent_settings = {
                'show_assignments': bool(show_assignments),
                'show_fees': bool(show_fees),
                'ai_summaries': bool(ai_summaries),
                'email_notifications': bool(email_notif),
                'sms_notifications': bool(sms_notif),
            }
            st.success("Parent settings saved")
