"""
Teacher Dashboard - Class management, marks entry, attendance, and student analytics.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from src.database.db_manager import DatabaseManager
from src.components.ui_components import (
    kpi_card, section_header, page_header, render_sidebar_nav, alert_card
)
from src.analytics.analytics_engine import (
    attendance_trend_chart, student_marks_bar, subject_performance_chart,
    grade_distribution_chart, performance_trend_chart
)
from src.utils.helpers import grade_from_score, risk_level, risk_color


def render_teacher_dashboard():
    """Render the Teacher dashboard."""
    user = st.session_state.user
    db = DatabaseManager()

    nav_items = [
        {"label": "🏠 Dashboard", "page": "Dashboard"},
        {"label": "👨‍🎓 My Students", "page": "My Students"},
        {"label": "📝 Add Marks", "page": "Add Marks"},
        {"label": "📅 Attendance", "page": "Attendance"},
        {"label": "📊 Analytics", "page": "Analytics"},
        {"label": "🤖 AI Assistant", "page": "AI Assistant"},
        {"label": "⚙️ Settings", "page": "Settings"},
    ]

    render_sidebar_nav(
        nav_items,
        role_label="Teacher",
        user_name=user["full_name"],
        school_name=user.get("school_name", ""),
    )

    page = st.session_state.get("page", "Dashboard")

    if page == "Dashboard":
        _render_teacher_overview(db, user)
    elif page == "My Students":
        _render_my_students(db, user)
    elif page == "Add Marks":
        _render_add_marks(db, user)
    elif page == "Attendance":
        _render_mark_attendance(db, user)
    elif page == "Analytics":
        _render_class_analytics(db, user)
    elif page == "AI Assistant":
        _render_ai_assistant(db, user)
    elif page == "Settings":
        _render_settings(db, user)


def _get_teacher_classes(db: DatabaseManager, user: dict) -> list:
    """Get classes assigned to this teacher."""
    school_id = user.get("school_id", 1)
    all_classes = db.get_all_classes(school_id=school_id)
    # Filter by teacher
    teacher_classes = [c for c in all_classes if c.get("teacher_id") == user.get("user_id")]
    if not teacher_classes:
        teacher_classes = all_classes[:2]  # Fallback for demo
    return teacher_classes


def _render_teacher_overview(db: DatabaseManager, user: dict):
    page_header(f"Welcome, {user['full_name']}", "Your class dashboard and student insights", "👩‍🏫")
    teacher_classes = _get_teacher_classes(db, user)
    school_id = user.get("school_id", 1)
    total_students = sum(c.get("student_count", 0) for c in teacher_classes)

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("My Classes", str(len(teacher_classes)), "Assigned classes", "🏫", "#00ff88")
    with c2:
        kpi_card("My Students", str(total_students), "Total enrolled", "👨‍🎓", "#00b4d8")
    with c3:
        # Attendance rate across my classes
        att_data = db.get_class_attendance_summary(school_id=school_id, days=30)
        my_class_labels = {f"{c['class_name']} {c['section']}" for c in teacher_classes}
        my_att = [a for a in att_data if a["class_label"] in my_class_labels]
        avg_att = round(sum(a["attendance_rate"] for a in my_att) / len(my_att), 1) if my_att else 0
        kpi_card("Avg Attendance", f"{avg_att}%", "My classes", "📅",
                 "#00ff88" if avg_att >= 80 else "#ffa502")
    with c4:
        # Weak students in my classes
        weak = db.get_weak_students(school_id=school_id, threshold=50)
        my_students_ids = set()
        for cls in teacher_classes:
            for s in db.get_students_by_class(cls["class_id"]):
                my_students_ids.add(s["student_id"])
        my_weak = [s for s in weak if s["student_id"] in my_students_ids]
        kpi_card("Weak Students", str(len(my_weak)), "Below 50% average", "⚠️",
                 "#ff4757" if my_weak else "#00ff88")

    st.markdown("---")

    col1, col2 = st.columns([3, 2])

    with col1:
        section_header("Class Summary", "", "📋")
        for cls in teacher_classes:
            students = db.get_students_by_class(cls["class_id"])
            marks_all = []
            for s in students:
                marks = db.get_student_marks(s["student_id"])
                marks_all.extend(marks)
            avg = round(sum(m["percentage"] for m in marks_all) / len(marks_all), 1) if marks_all else 0

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0d1226,#111827); border:1px solid #1e2a45;
                        border-radius:12px; padding:16px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; justify-content:space-between;">
                    <div>
                        <h4 style="color:#ccd6f6;margin:0;">{cls['class_name']} {cls['section']}</h4>
                        <p style="color:#8892b0;font-size:0.85rem;margin:4px 0 0 0;">
                            👨‍🎓 {len(students)} students • 📅 {cls.get('academic_year','2024-25')}
                        </p>
                    </div>
                    <div style="text-align:right;">
                        <span style="background:#00ff8820;color:#00ff88;border-radius:8px;padding:4px 12px;font-weight:700;">{avg}%</span>
                        <p style="color:#8892b0;font-size:0.75rem;margin:4px 0 0 0;">Class avg</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        section_header("Students Needing Help", "", "🆘")
        if my_weak:
            for s in my_weak[:6]:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:8px 0;
                            border-bottom:1px solid #1e2a45;">
                    <span style="font-size:1.2rem;">⚠️</span>
                    <div style="flex:1;">
                        <p style="color:#ccd6f6;margin:0;font-size:0.85rem;">{s['full_name']}</p>
                        <p style="color:#8892b0;margin:0;font-size:0.75rem;">{s.get('class_name','')} • Avg: {s['avg_score']}%</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ All your students are performing above 50%!")

        st.markdown("---")
        trend = db.get_attendance_trend(school_id=school_id, days=14)
        st.plotly_chart(attendance_trend_chart(trend), use_container_width=True)

    # Notifications for teachers
    section_header("Announcements & Notifications", "School updates for staff", "🔔")
    notifs = db.get_notifications_for_role(school_id=school_id, role='teacher', limit=10)
    if notifs:
        for notif in notifs:
            alert_card(title=notif['title'], message=notif['message'], severity='medium', time_str=time_ago(notif.get('created_at')))
    else:
        st.info("No notifications at this time.")


def _render_my_students(db: DatabaseManager, user: dict):
    page_header("My Students", "All students in your assigned classes", "👨‍🎓")

    teacher_classes = _get_teacher_classes(db, user)
    school_id = user.get("school_id", 1)
    if not teacher_classes:
        st.info("No classes assigned to you yet.")
        return

    class_options = {f"{c['class_name']} {c['section']}": c["class_id"] for c in teacher_classes}
    selected = st.selectbox("Select Class", list(class_options.keys()))
    class_id = class_options[selected]
    students = db.get_students_by_class(class_id)

    if not students:
        st.info("No students in this class.")
        return

    # Build performance table
    rows = []
    for s in students:
        marks = db.get_student_marks(s["student_id"])
        att = db.get_attendance_rate(s["student_id"], 30)
        avg = round(sum(m["percentage"] for m in marks) / len(marks), 1) if marks else 0
        rows.append({
            "Name": s["full_name"],
            "Gender": s.get("gender", ""),
            "Age": s.get("age", ""),
            "Avg Score": avg,
            "Grade": grade_from_score(avg),
            "Attendance": f"{att}%",
            "Risk Level": risk_level(avg, att),
            "Study Hrs": s.get("study_hours", "N/A"),
            "student_id": s["student_id"],
        })

    df = pd.DataFrame(rows)

    # Summary KPIs
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Students", str(len(rows)), "In selected class", "👨‍🎓", "#00ff88")
    with c2:
        avg_cls = round(df["Avg Score"].mean(), 1) if not df.empty else 0
        kpi_card("Class Avg", f"{avg_cls}%", "Overall performance", "📊",
                 "#00ff88" if avg_cls >= 65 else "#ffa502")
    with c3:
        at_risk = df[df["Avg Score"] < 50].shape[0]
        kpi_card("At Risk", str(at_risk), "Below 50% average", "⚠️",
                 "#ff4757" if at_risk > 0 else "#00ff88")

    st.dataframe(df.drop(columns=["student_id"]), use_container_width=True, height=380)

    # Student detail
    st.markdown("---")
    section_header("Student Detail", "", "👤")
    name_map = {r["student_id"]: r["Name"] for r in rows}
    sel_id = st.selectbox("Select Student for Detail", options=list(name_map.keys()),
                           format_func=lambda x: name_map[x], key="teacher_student_detail")
    if sel_id:
        marks = db.get_student_marks(sel_id)
        att = db.get_attendance_rate(sel_id, 30)
        avg = round(sum(m["percentage"] for m in marks) / len(marks), 1) if marks else 0

        col1, col2 = st.columns(2)
        with col1:
            if marks:
                st.plotly_chart(student_marks_bar(marks, name_map[sel_id]), use_container_width=True)
        with col2:
            if marks:
                st.plotly_chart(performance_trend_chart(marks, name_map[sel_id]), use_container_width=True)

        rl = risk_level(avg, att)
        if rl in ("🔴 Critical", "🟠 High"):
            st.error(f"⚠️ **{name_map[sel_id]}** is at {rl} risk. Recommend immediate teacher intervention and parent notification.")
        elif rl == "🟡 Medium":
            st.warning(f"📋 **{name_map[sel_id]}** needs monitoring. Schedule a check-in session.")


def _render_add_marks(db: DatabaseManager, user: dict):
    page_header("Add Student Marks", "Record examination results", "📝")

    teacher_classes = _get_teacher_classes(db, user)
    class_options = {f"{c['class_name']} {c['section']}": c["class_id"] for c in teacher_classes}

    col1, col2 = st.columns(2)
    with col1:
        selected_class_name = st.selectbox("Select Class", list(class_options.keys()), key="marks_class")
    class_id = class_options[selected_class_name]
    students = db.get_students_by_class(class_id)
    subjects = db.get_subjects_by_class(class_id)

    if not students or not subjects:
        st.warning("No students or subjects found for this class.")
        return

    # Bulk marks entry table
    section_header("Enter Marks", "One student at a time", "✏️")

    with st.form("add_marks_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            student_map = {s["student_id"]: s["full_name"] for s in students}
            student_id = st.selectbox("Student", options=list(student_map.keys()),
                                       format_func=lambda x: student_map[x])
        with col2:
            subject_map = {s["subject_id"]: s["subject_name"] for s in subjects}
            subject_id = st.selectbox("Subject", options=list(subject_map.keys()),
                                       format_func=lambda x: subject_map[x])
        with col3:
            exam_type = st.selectbox("Exam Type", ["mid_term", "final", "quiz", "assignment"])

        col4, col5, col6 = st.columns(3)
        with col4:
            marks_obtained = st.number_input("Marks Obtained", min_value=0.0, max_value=200.0, value=75.0)
        with col5:
            total_marks = st.number_input("Total Marks", min_value=1.0, max_value=200.0, value=100.0)
        with col6:
            exam_date = st.date_input("Exam Date", value=date.today())

        pct = round((marks_obtained / total_marks) * 100, 1) if total_marks > 0 else 0
        st.info(f"📊 Calculated percentage: **{pct}%** — Grade: **{grade_from_score(pct)}**")

        if st.form_submit_button("💾 Save Marks", use_container_width=True):
            db.add_marks(
                student_id=student_id,
                subject_id=subject_id,
                exam_type=exam_type,
                marks_obtained=marks_obtained,
                total_marks=total_marks,
                exam_date=exam_date.strftime("%Y-%m-%d"),
                recorded_by=user["user_id"],
            )
            st.success(f"✅ Marks saved for {student_map[student_id]}!")

    # Recent marks
    st.markdown("---")
    section_header("Recent Marks (This Class)", "", "📋")
    all_marks = []
    for s in students[:10]:
        for m in db.get_student_marks(s["student_id"])[:3]:
            all_marks.append({
                "Student": s["full_name"],
                "Subject": m.get("subject_name", ""),
                "Exam": m.get("exam_type", ""),
                "Score": m.get("marks_obtained", 0),
                "Total": m.get("total_marks", 100),
                "Percentage": f"{m.get('percentage', 0):.1f}%",
                "Grade": grade_from_score(m.get("percentage", 0)),
                "Date": m.get("exam_date", ""),
            })
    if all_marks:
        st.dataframe(pd.DataFrame(all_marks), use_container_width=True, height=300)


def _render_mark_attendance(db: DatabaseManager, user: dict):
    page_header("Mark Attendance", "Record daily student attendance", "📅")

    teacher_classes = _get_teacher_classes(db, user)
    class_options = {f"{c['class_name']} {c['section']}": c["class_id"] for c in teacher_classes}

    col1, col2 = st.columns(2)
    with col1:
        selected_class_name = st.selectbox("Select Class", list(class_options.keys()), key="att_class")
    with col2:
        att_date = st.date_input("Date", value=date.today())

    class_id = class_options[selected_class_name]
    students = db.get_students_by_class(class_id)

    if not students:
        st.info("No students in this class.")
        return

    st.markdown(f"**Marking attendance for {len(students)} students**")

    with st.form("attendance_form"):
        attendance_data = {}
        for student in students:
            col_name, col_status = st.columns([3, 1])
            with col_name:
                # Show existing attendance
                existing = db.get_student_attendance(student["student_id"], days=1)
                existing_status = existing[0]["status"] if existing else None
                st.markdown(f"**{student['full_name']}**")
            with col_status:
                status = st.selectbox(
                    "Status",
                    ["present", "absent", "late"],
                    index=["present", "absent", "late"].index(existing_status) if existing_status else 0,
                    key=f"att_{student['student_id']}",
                    label_visibility="collapsed",
                )
            attendance_data[student["student_id"]] = status

        if st.form_submit_button("💾 Save Attendance", use_container_width=True):
            for sid, status in attendance_data.items():
                db.add_attendance(sid, class_id, att_date.strftime("%Y-%m-%d"),
                                  status, user["user_id"])
            present_count = sum(1 for s in attendance_data.values() if s == "present")
            st.success(f"✅ Attendance saved! Present: {present_count}/{len(students)}")
            st.rerun()

    # Summary chart
    st.markdown("---")
    school_id = user.get("school_id", 1)
    trend = db.get_attendance_trend(school_id=school_id, days=14)
    st.plotly_chart(attendance_trend_chart(trend), use_container_width=True)


def _render_class_analytics(db: DatabaseManager, user: dict):
    page_header("Class Analytics", "Performance insights for your classes", "📊")

    teacher_classes = _get_teacher_classes(db, user)
    class_options = {f"{c['class_name']} {c['section']}": c["class_id"] for c in teacher_classes}
    selected = st.selectbox("Select Class", list(class_options.keys()))
    class_id = class_options[selected]
    students = db.get_students_by_class(class_id)

    if not students:
        st.info("No data available.")
        return

    # Aggregate marks
    all_marks = []
    for s in students:
        for m in db.get_student_marks(s["student_id"]):
            all_marks.append({"percentage": m["percentage"]})

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(grade_distribution_chart(all_marks), use_container_width=True)
    with col2:
        school_id = user.get("school_id", 1)
        subj_data = db.get_subject_performance(school_id=school_id)
        st.plotly_chart(subject_performance_chart(subj_data), use_container_width=True)

    # Weak students list
    section_header("Students Needing Support", "", "⚠️")
    weak_rows = []
    for s in students:
        marks = db.get_student_marks(s["student_id"])
        avg = round(sum(m["percentage"] for m in marks) / len(marks), 1) if marks else 0
        att = db.get_attendance_rate(s["student_id"], 30)
        if avg < 60 or att < 75:
            weak_rows.append({
                "Name": s["full_name"],
                "Avg Score": avg,
                "Attendance": f"{att}%",
                "Risk": risk_level(avg, att),
                "Recommendation": "Extra tutoring" if avg < 50 else "Monitor progress",
            })

    if weak_rows:
        st.dataframe(pd.DataFrame(weak_rows), use_container_width=True)
    else:
        st.success("✅ All students in this class are meeting expectations!")


def _render_ai_assistant(db: DatabaseManager, user: dict):
    school_id = user.get("school_id", 1)
    stats = db.get_school_summary(school_id=school_id)

    # Gather teacher-specific context: classes, weak students, subject performance, attendance trends
    teacher_classes = _get_teacher_classes(db, user)
    class_list = []
    class_ids = [c["class_id"] for c in teacher_classes]
    for c in teacher_classes:
        cid = c.get("class_id")
        students = db.get_students_by_class(cid)
        student_count = len(students)
        # class subject averages
        subj_summary = db.get_class_marks_summary(cid)
        class_list.append({
            "class_id": cid,
            "label": f"{c.get('class_name')} {c.get('section')}",
            "student_count": student_count,
            "subject_averages": subj_summary,
        })

    # Weak students in my classes
    weak_all = db.get_weak_students(school_id=school_id, threshold=50)
    weak_my = [w for w in weak_all if w.get('student_id') and any(w.get('class_name') == cls.get('class_name') and w.get('section') == cls.get('section') for cls in teacher_classes)]

    # Attendance drops: compare 60-day vs 30-day attendance per student and surface drops >15%
    attendance_drops = []
    for cid in class_ids:
        for s in db.get_students_by_class(cid):
            sid = s.get('student_id')
            rate_60 = db.get_attendance_rate(sid, days=60)
            rate_30 = db.get_attendance_rate(sid, days=30)
            if rate_60 and rate_30 and (rate_60 - rate_30) >= 15:
                attendance_drops.append({
                    "student_id": sid,
                    "full_name": s.get('full_name'),
                    "class": f"{s.get('class_name','')} {s.get('section','')}",
                    "drop_percent": round(rate_60 - rate_30, 1),
                    "rate_60": rate_60,
                    "rate_30": rate_30,
                })

    context = {
        "school_info": {"school_name": user.get("school_name", "")},
        "stats": stats,
        "teacher_info": {"user_id": user.get("user_id"), "name": user.get("full_name")},
        "classes": class_list,
        "weak_students": weak_my,
        "attendance_drops": attendance_drops,
    }

    from src.chatbot.groq_chatbot import SchoolChatbot, render_chatbot_ui

    # Quick action suggestions for teachers
    st.markdown("**💡 Quick actions for teachers**")
    col1, col2 = st.columns(2)
    chatbot = SchoolChatbot()

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    def send_and_append(prompt_text: str):
        resp = chatbot.chat(prompt_text, st.session_state.get('chat_history', []), context or context)
        st.session_state.chat_history.append({"role": "user", "content": prompt_text})
        st.session_state.chat_history.append({"role": "assistant", "content": resp})
        st.experimental_rerun()

    with col1:
        if st.button("Identify weak students in my classes", use_container_width=True):
            send_and_append("Identify weak students in my classes and suggest interventions.")
        if st.button("Recommend improvement plans for weak students", use_container_width=True, key="plan"):
            send_and_append("Recommend improvement plans for the weak students listed in my classes.")

    with col2:
        if st.button("Analyze recent attendance drops", use_container_width=True):
            send_and_append("Analyze recent attendance drops in my classes and recommend interventions.")
        if st.button("Suggest revision sessions for Math", use_container_width=True):
            send_and_append("Suggest a plan for revision sessions for Math across my classes, including frequency and content focus.")

    # Finally render the full chatbot UI with provided context
    render_chatbot_ui(context)


def _render_settings(db: DatabaseManager, user: dict):
    """Teacher settings: subject preferences and notification toggles."""
    page_header("Settings", "Customize your teacher preferences", "⚙️")

    with st.form("teacher_settings_form"):
        st.markdown("**Subject Preferences**")
        # fetch subjects in school
        subjects = []
        try:
            subjects = db.get_subject_performance(school_id=user.get('school_id', 1))
            subject_names = [s['subject_name'] for s in subjects]
        except Exception:
            subject_names = ["Mathematics", "English", "Science"]

        pref = st.multiselect("Subjects you prefer to teach / follow", options=subject_names, default=subject_names[:2])

        st.markdown("**Notifications**")
        email_notif = st.checkbox("Email notifications for AI alerts", value=True)
        push_notif = st.checkbox("In-app notifications for attendance drops", value=True)
        digest = st.selectbox("Weekly digest day", ["Monday","Tuesday","Wednesday","Thursday","Friday"], index=0)

        if st.form_submit_button("Save Settings"):
            # Persist to session for now; can be expanded to DB-backed storage
            st.session_state.teacher_settings = {
                'preferred_subjects': pref,
                'email_notifications': bool(email_notif),
                'push_notifications': bool(push_notif),
                'digest_day': digest,
            }
            st.success("Teacher settings saved")
