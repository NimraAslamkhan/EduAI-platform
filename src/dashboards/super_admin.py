"""
Super Admin Dashboard - System-wide management and monitoring.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.database.db_manager import DatabaseManager
from src.components.ui_components import (
    kpi_card, section_header, page_header, render_sidebar_nav, alert_card
)
from src.analytics.analytics_engine import (
    attendance_trend_chart, grade_distribution_chart, class_comparison_chart,
    fee_collection_chart, risk_scatter_chart, heatmap_attendance
)
from src.utils.helpers import format_currency, time_ago


def render_super_admin_dashboard():
    """Render the Super Admin dashboard."""
    user = st.session_state.user
    db = DatabaseManager()

    nav_items = [
        {"label": "🏠 System Overview", "page": "Dashboard"},
        {"label": "🎒 Students", "page": "Students"},
        {"label": "👩‍🏫 Teachers", "page": "Teachers"},
        {"label": "🏫 School Management", "page": "Schools"},
        {"label": "👥 User Management", "page": "Users"},
        {"label": "📊 Global Analytics", "page": "Analytics"},
        {"label": "💰 Fee Reports", "page": "Fees"},
        {"label": "🤖 AI Assistant", "page": "AI Assistant"},
        {"label": "🔔 Alerts", "page": "Alerts"},
        {"label": "🔔 Notifications", "page": "Notifications"},
        {"label": "⚙️ System Settings", "page": "Settings"},
    ]

    render_sidebar_nav(
        nav_items,
        role_label="Super Administrator",
        user_name=user["full_name"],
        school_name="EduAI Platform",
    )

    page = st.session_state.get("page", "Dashboard")

    if page == "Dashboard":
        _render_system_overview(db, user)
    elif page == "Students":
        _render_student_management(db)
    elif page == "Teachers":
        _render_teacher_management(db)
    elif page == "Schools":
        _render_school_management(db)
    elif page == "Users":
        _render_user_management(db)
    elif page == "Analytics":
        _render_global_analytics(db)
    elif page == "Fees":
        _render_fee_reports(db)
    elif page == "AI Assistant":
        _render_ai_assistant(db, user)
    elif page == "Alerts":
        from src.alerts.alert_system import render_alerts_page
        render_alerts_page(school_id=1)
    elif page == "Notifications":
        _render_notifications_admin(db)
    elif page == "Settings":
        _render_system_settings()


def _render_system_overview(db: DatabaseManager, user: dict):
    page_header(
        "System Overview",
        "EduAI Platform — Real-time school intelligence dashboard",
        badge="⚡ Super Admin"
    )

    stats = db.get_school_summary(school_id=1)

    # Top KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Total Students", str(stats["total_students"]), "Enrolled & active", "👨‍🎓", "#00ff88")
    with c2:
        kpi_card("Total Teachers", str(stats["total_teachers"]), "Teaching staff", "👩‍🏫", "#00b4d8")
    with c3:
        kpi_card("Total Classes", str(stats["total_classes"]), "Active classes", "🏫", "#7b5ea7")
    with c4:
        kpi_card("Attendance Rate", f"{stats['attendance_rate']}%", "Last 30 days", "📅",
                 "#00ff88" if stats["attendance_rate"] >= 80 else "#ffa502")
    with c5:
        kpi_card("Avg Performance", f"{stats['avg_marks']}%", "All students", "📊",
                 "#00ff88" if stats["avg_marks"] >= 65 else "#ff6348")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        section_header("Attendance Trend", "Last 30 days", "📅")
        trend = db.get_attendance_trend(school_id=1, days=30)
        st.plotly_chart(attendance_trend_chart(trend), use_container_width=True)

        section_header("Fee Collection Overview", "", "💰")
        fee_data = db.get_fee_summary(school_id=1)
        st.plotly_chart(fee_collection_chart(fee_data), use_container_width=True)

    with col2:
        section_header("Class Performance Heatmap", "", "🔥")
        class_att = db.get_class_attendance_summary(school_id=1, days=30)
        st.plotly_chart(heatmap_attendance(class_att), use_container_width=True)

        section_header("Recent Alerts", "", "🔔")
        alerts = db.get_ai_alerts(school_id=1, resolved=False)
        if alerts:
            for alert in alerts[:4]:
                alert_card(
                    title=alert["title"],
                    message=alert["message"][:80] + "...",
                    severity=alert["severity"],
                    student=alert.get("student_name", ""),
                    time_str=time_ago(alert["created_at"]) if alert.get("created_at") else "",
                )
        else:
            st.success("✅ No active alerts!")

    st.markdown("---")

    col3, col4 = st.columns(2)
    with col3:
        section_header("Grade Distribution", "", "📊")
        ml_data = db.get_performance_data_for_ml(school_id=1)
        marks_dist = [{"percentage": d["avg_score"]} for d in ml_data if d.get("avg_score")]
        st.plotly_chart(grade_distribution_chart(marks_dist), use_container_width=True)

    with col4:
        section_header("Risk Analysis", "", "🎯")
        st.plotly_chart(risk_scatter_chart(ml_data), use_container_width=True)


def _render_school_management(db: DatabaseManager):
    page_header("School Management", "Manage registered schools", "🏫")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM schools")
        schools = [dict(r) for r in cursor.fetchall()]

    if schools:
        df = pd.DataFrame(schools)
        st.dataframe(df[["school_id", "name", "address", "phone", "email", "established_year"]],
                     use_container_width=True)

    st.markdown("---")
    section_header("Add New School", "", "➕")
    with st.form("add_school"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("School Name *")
            phone = st.text_input("Phone")
            year = st.number_input("Established Year", min_value=1900, max_value=2025, value=2010)
        with col2:
            address = st.text_area("Address")
            email = st.text_input("Email")

        if st.form_submit_button("➕ Add School"):
            if not name:
                st.error("School name is required!")
            else:
                with db.get_connection() as conn:
                    conn.execute(
                        "INSERT INTO schools (name, address, phone, email, established_year) VALUES (?,?,?,?,?)",
                        (name, address, phone, email, year)
                    )
                st.success(f"✅ School '{name}' added!")
                st.rerun()


def _render_user_management(db: DatabaseManager):
    page_header("User Management", "All platform users across roles", "👥")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.full_name, u.email, u.role, u.is_active, u.created_at,
                   s.name as school_name
            FROM users u
            LEFT JOIN schools s ON u.school_id = s.school_id
            ORDER BY u.role, u.full_name
        """)
        users = [dict(r) for r in cursor.fetchall()]

    if not users:
        st.info("No users found.")
        return

    # Role breakdown
    df = pd.DataFrame(users)
    role_counts = df.groupby("role").size().reset_index(name="count")

    c1, c2, c3, c4 = st.columns(4)
    role_icons = {"super_admin": "👑", "principal": "🎓", "teacher": "👩‍🏫", "parent": "👨‍👩‍👧"}
    role_colors = {"super_admin": "#7b5ea7", "principal": "#00ff88",
                   "teacher": "#00b4d8", "parent": "#ffa502"}

    for i, (_, row) in enumerate(role_counts.iterrows()):
        with [c1, c2, c3, c4][i % 4]:
            kpi_card(
                row["role"].replace("_", " ").title(),
                str(row["count"]),
                "users",
                role_icons.get(row["role"], "👤"),
                role_colors.get(row["role"], "#ccd6f6"),
            )

    st.markdown("---")

    # Filter
    role_filter = st.selectbox("Filter by Role", ["All", "super_admin", "principal", "teacher", "parent"])
    filtered = df if role_filter == "All" else df[df["role"] == role_filter]

    display = filtered[["user_id", "full_name", "email", "role", "school_name", "is_active", "created_at"]].rename(columns={
        "user_id": "ID", "full_name": "Name", "email": "Email",
        "role": "Role", "school_name": "School",
        "is_active": "Active", "created_at": "Created At"
    })
    st.dataframe(display, use_container_width=True, height=400)
    st.caption(f"Showing {len(display)} users")


def _render_notifications_admin(db: DatabaseManager):
    page_header("Notifications", "Create and manage school-wide notifications", "🔔")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 50")
        existing = [dict(r) for r in cursor.fetchall()]

    st.subheader("Create Notification")
    with st.form("create_notif"):
        title = st.text_input("Title *")
        ntype = st.selectbox("Type", ["info", "warning", "alert", "success"], index=0)
        target_role = st.selectbox("Target Role", ["all", "principal", "teacher", "parent", "super_admin"], index=0)
        message = st.text_area("Message *", height=120)
        if st.form_submit_button("Send Notification"):
            if not title or not message:
                st.error("Title and message are required")
            else:
                tr = None if target_role == "all" else target_role
                with db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO notifications (school_id, user_id, title, message, type, target_role) VALUES (?,?,?,?,?,?)",
                        (1, None, title, message, ntype, tr)
                    )
                st.success("Notification created and dispatched")
                st.rerun()

    st.markdown("---")
    st.subheader("Recent Notifications")
    if existing:
        for notif in existing:
            st.markdown(f"**{notif['title']}** — {notif['type'].upper()} — {notif.get('target_role') or 'all'}")
            st.write(notif['message'])
            st.caption(str(notif.get('created_at')))
            st.markdown("---")
    else:
        st.info("No notifications yet.")


def _render_student_management(db: DatabaseManager):
    page_header("Student Management", "Upload, validate, edit and manage students", "🎒")

    tab1, tab2 = st.tabs(["📥 Upload CSV", "🧾 Existing Students"])

    with tab1:
        section_header("Upload Student CSV", "Columns supported: name,class,section,age,gender,parent_contact,phone,extracurricular_activity,status,study_hours", "📤")
        uploaded = st.file_uploader("Choose CSV file", type=["csv"]) 
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded)
            except Exception as e:
                st.error(f"Failed to parse CSV: {e}")
                return

            st.markdown("**Preview (first 10 rows)**")
            st.dataframe(df.head(10))

            # Normalize column names
            cols = {c.strip().lower(): c for c in df.columns}
            required = ["name"]
            missing_required = [r for r in required if r not in cols]
            if missing_required:
                st.error(f"Missing required columns: {', '.join(missing_required)}")
            else:
                # Basic cleaning: fill missing values
                cleaned = df.rename(columns={cols[k]: k for k in cols})
                cleaned = cleaned.fillna({"age": 0, "gender": "Not specified", "status": "active", "study_hours": 3.0})

                # Validate rows
                errors = []
                for i, row in cleaned.iterrows():
                    if not row.get("name") or str(row.get("name")).strip() == "":
                        errors.append((i, "Missing name"))

                if errors:
                    st.warning(f"Found {len(errors)} invalid rows. Please fix and re-upload.")
                    st.table(pd.DataFrame(errors, columns=["row","error"]))
                else:
                    if st.button("Import Students to DB"):
                        imported = 0
                        for _, r in cleaned.iterrows():
                            # Resolve class -> class_id
                            class_name = str(r.get("class") or r.get("class_name") or "").strip()
                            section = str(r.get("section") or "A").strip()
                            with db.get_connection() as conn:
                                cur = conn.cursor()
                                if class_name:
                                    cur.execute("SELECT class_id FROM classes WHERE school_id=? AND class_name=? AND section=?",
                                                (1, class_name, section))
                                    c = cur.fetchone()
                                    if c:
                                        class_id = c[0]
                                    else:
                                        cur.execute("INSERT INTO classes (school_id, class_name, section, academic_year) VALUES (?,?,?,?)",
                                                    (1, class_name, section, "2024-25"))
                                        class_id = cur.lastrowid
                                else:
                                    class_id = None

                                # Resolve parent contact -> try email, else leave null
                                parent_contact = str(r.get("parent_contact") or "").strip()
                                parent_id = None
                                if "@" in parent_contact:
                                    cur.execute("SELECT user_id FROM users WHERE email=?", (parent_contact.lower(),))
                                    p = cur.fetchone()
                                    if p:
                                        parent_id = p[0]
                                    else:
                                        # create parent user
                                        cur.execute("INSERT INTO users (school_id, full_name, email, password_hash, role) VALUES (?,?,?,?,?)",
                                                    (1, parent_contact.split("@")[0], parent_contact.lower(), db._hash_password("changeme123"), "parent"))
                                        parent_id = cur.lastrowid

                                # Insert student
                                full_name = str(r.get("name")).strip()
                                age = int(r.get("age") or 0)
                                gender = str(r.get("gender") or "Not specified")
                                address = str(r.get("address") or "")
                                phone = str(r.get("phone") or "")
                                study_hours = float(r.get("study_hours") or 3.0)
                                cur.execute(
                                    "INSERT INTO students (school_id, class_id, parent_id, full_name, age, gender, address, phone, enrollment_date, study_hours, status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                    (1, class_id, parent_id, full_name, age, gender, address, phone, datetime.now().strftime("%Y-%m-%d"), study_hours, str(r.get("status") or "active"))
                                )
                                imported += 1

                        st.success(f"Imported {imported} students")
                        st.rerun()

    with tab2:
        page_header("Existing Students", "Edit, update or soft-delete student records", "🧾")
        students = db.get_all_students(school_id=1)
        if not students:
            st.info("No students found.")
            return
        df = pd.DataFrame(students)
        st.dataframe(df[["student_id","full_name","class_name","section","age","gender","phone","status"]], use_container_width=True, height=350)

        sel = st.selectbox("Select student to edit", options=[s["student_id"] for s in students], format_func=lambda x: next((s["full_name"] for s in students if s["student_id"]==x), str(x)))
        if sel:
            s = next(s for s in students if s["student_id"] == sel)
            with st.form("edit_student"):
                name = st.text_input("Full name", value=s.get("full_name", ""))
                age = st.number_input("Age", min_value=0, max_value=30, value=s.get("age") or 0)
                gender = st.selectbox("Gender", ["Male","Female","Not specified"], index=0 if s.get("gender","")=="Male" else (1 if s.get("gender","")=="Female" else 2))
                phone = st.text_input("Phone", value=s.get("phone",""))
                status = st.selectbox("Status", ["active","inactive","graduated"], index=["active","inactive","graduated"].index(s.get("status") or "active"))
                if st.form_submit_button("Update Student"):
                    db.update_student(sel, full_name=name, age=age, gender=gender, phone=phone, status=status)
                    st.success("Student updated")
                    st.rerun()
                if st.button("Delete (soft)"):
                    db.delete_student(sel)
                    st.success("Student marked inactive")
                    st.rerun()


def _render_teacher_management(db: DatabaseManager):
    page_header("Teacher Management", "Manage teachers, assign subjects and classes", "👩‍🏫")

    teachers = db.get_all_teachers(school_id=1)
    if not teachers:
        st.info("No teachers found.")
        return

    teacher_map = {t["user_id"]: t for t in teachers}
    sel = st.selectbox("Select Teacher", options=list(teacher_map.keys()), format_func=lambda x: teacher_map[x]["full_name"]) 
    t = teacher_map[sel]

    # list classes and subjects
    classes = db.get_all_classes(school_id=1)
    class_options = {f"{c['class_name']} {c['section']}": c['class_id'] for c in classes}
    subjects = []
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT subject_id, subject_name, class_id, teacher_id FROM subjects WHERE school_id=?", (1,))
        subjects = [dict(r) for r in cur.fetchall()]

    # Preselect classes currently assigned to teacher
    assigned_class_ids = [c['class_id'] for c in classes if c.get('teacher_id') == t['user_id']]
    assigned_subject_ids = [s['subject_id'] for s in subjects if s.get('teacher_id') == t['user_id']]

    st.markdown(f"**Teacher:** {t['full_name']} — {t.get('email','')}")
    with st.form("assign_teacher"):
        chosen_classes = st.multiselect("Assign Classes (will set class.teacher_id)", options=list(class_options.keys()), default=[k for k,v in class_options.items() if v in assigned_class_ids])
        subj_map = {f"{s['subject_name']} (class:{s['class_id']})": s['subject_id'] for s in subjects}
        chosen_subjects = st.multiselect("Assign Subjects (will set subject.teacher_id)", options=list(subj_map.keys()), default=[k for k,v in subj_map.items() if v in assigned_subject_ids])

        if st.form_submit_button("Save Assignments"):
            # Clear previous assignments for this teacher on selected scope
            with db.get_connection() as conn:
                cur = conn.cursor()
                # Update classes
                cur.execute("UPDATE classes SET teacher_id=NULL WHERE teacher_id=?", (t['user_id'],))
                for cls_name in chosen_classes:
                    cid = class_options.get(cls_name)
                    if cid:
                        cur.execute("UPDATE classes SET teacher_id=? WHERE class_id=?", (t['user_id'], cid))

                # Update subjects
                cur.execute("UPDATE subjects SET teacher_id=NULL WHERE teacher_id=?", (t['user_id'],))
                for sk in chosen_subjects:
                    sid = subj_map.get(sk)
                    if sid:
                        cur.execute("UPDATE subjects SET teacher_id=? WHERE subject_id=?", (t['user_id'], sid))

            st.success("Assignments saved")
            st.rerun()


def _render_global_analytics(db: DatabaseManager):
    page_header("Global Analytics", "School-wide performance analysis", "📊")

    tab1, tab2, tab3 = st.tabs(["📊 Performance", "📅 Attendance", "🎯 Risk Analysis"])

    with tab1:
        ml_data = db.get_performance_data_for_ml(school_id=1)
        marks_dist = [{"percentage": d["avg_score"]} for d in ml_data if d.get("avg_score")]

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(grade_distribution_chart(marks_dist), use_container_width=True)
        with col2:
            from src.analytics.analytics_engine import subject_performance_chart
            subj = db.get_subject_performance(school_id=1)
            st.plotly_chart(subject_performance_chart(subj), use_container_width=True)

        # Top performers
        section_header("Top 10 Students", "", "⭐")
        top = db.get_top_students(school_id=1, limit=10)
        if top:
            df = pd.DataFrame(top)
            df.columns = ["ID", "Name", "Class", "Section", "Avg Score (%)"]
            st.dataframe(df, use_container_width=True)

    with tab2:
        trend = db.get_attendance_trend(school_id=1, days=30)
        st.plotly_chart(attendance_trend_chart(trend), use_container_width=True)

        class_att = db.get_class_attendance_summary(school_id=1, days=30)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(class_comparison_chart(class_att), use_container_width=True)
        with col2:
            st.plotly_chart(heatmap_attendance(class_att), use_container_width=True)

    with tab3:
        st.plotly_chart(risk_scatter_chart(ml_data), use_container_width=True)

        # ML predictions
        section_header("AI Predictions", "", "🤖")
        from src.ml.ml_pipeline import StudentMLPipeline
        pipeline = StudentMLPipeline()
        if not pipeline.is_trained:
            with st.spinner("Training ML models..."):
                metrics = pipeline.train(ml_data)
            if "error" not in metrics:
                col1, col2, col3 = st.columns(3)
                with col1:
                    kpi_card("Performance Model", f"{metrics.get('performance_accuracy', 'N/A')}%",
                             "Accuracy", "🤖", "#00ff88")
                with col2:
                    kpi_card("Dropout Model", f"{metrics.get('dropout_accuracy', 'N/A')}%",
                             "Accuracy", "🎯", "#00b4d8")
                with col3:
                    kpi_card("High Risk Students", str(metrics.get("high_risk_count", "N/A")),
                             "Detected", "⚠️", "#ff4757")

        importance = pipeline.get_feature_importance()
        if importance:
            section_header("Feature Importance", "Top factors affecting student performance", "🧠")
            sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            for feature, imp in sorted_imp:
                bar = min(100, imp)
                color = "#00ff88" if imp > 30 else "#00b4d8" if imp > 15 else "#7b5ea7"
                st.markdown(f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="color:#ccd6f6;font-size:0.9rem;">{feature}</span>
                        <span style="color:{color};font-weight:700;">{imp:.1f}%</span>
                    </div>
                    <div style="background:#1e2a45;border-radius:6px;height:8px;">
                        <div style="background:{color};width:{bar}%;height:100%;border-radius:6px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


def _render_fee_reports(db: DatabaseManager):
    page_header("Fee Reports", "Financial overview and collection status", "💰")

    fee_data = db.get_fee_summary(school_id=1)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Expected", format_currency(fee_data.get("total_expected") or 0),
                 "All fees", "💵", "#00ff88")
    with c2:
        kpi_card("Collected", format_currency(fee_data.get("total_collected") or 0),
                 "Received", "✅", "#00b4d8")
    with c3:
        kpi_card("Outstanding", format_currency(fee_data.get("total_pending") or 0),
                 "Unpaid balance", "⏳", "#ff4757")
    with c4:
        total = fee_data.get("total_expected") or 1
        col = fee_data.get("total_collected") or 0
        rate = round((col / total) * 100, 1)
        kpi_card("Collection Rate", f"{rate}%", "Of expected total", "📊",
                 "#00ff88" if rate >= 80 else "#ffa502")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fee_collection_chart(fee_data), use_container_width=True)
    with col2:
        st.markdown("**📋 Summary Breakdown**")
        st.metric("Paid Records", fee_data.get("paid_count") or 0)
        st.metric("Unpaid Records", fee_data.get("unpaid_count") or 0)
        st.metric("Partial Records", fee_data.get("partial_count") or 0)


def _render_ai_assistant(db: DatabaseManager, user: dict):
    stats = db.get_school_summary(school_id=1)
    context = {
        "school_info": {"school_name": "EduAI Platform"},
        "stats": stats,
    }
    from src.chatbot.groq_chatbot import render_chatbot_ui
    render_chatbot_ui(context)


def _render_system_settings():
    page_header("System Settings", "Platform configuration and preferences", "⚙️")

    tab1, tab2 = st.tabs(["🔧 General", "🔔 Notifications"])

    with tab1:
        # Allow selecting a school to update branding
        db = DatabaseManager()
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT school_id, name, logo_url FROM schools ORDER BY name")
            schools = [dict(r) for r in cur.fetchall()]

        school_map = {s['school_id']: s for s in schools} if schools else {}
        school_options = [f"{s['school_id']} - {s['name']}" for s in schools] if schools else []
        selected = None
        if school_options:
            sel = st.selectbox("Select School to configure", school_options)
            selected = int(sel.split(" - ")[0])

        st.text_input("Platform Name", value="EduAI Platform")
        st.text_input("Support Email", value="support@eduai.com")
        st.selectbox("Default Theme", ["Dark (Recommended)", "Light"])
        st.selectbox("Default Language", ["English"])
        st.selectbox("Timezone", ["UTC", "EST", "PST", "IST"])

        section_header("Branding", "Upload logo and update school display name", "🏷️")
        school_name = "" if not selected else school_map[selected]['name']
        logo_current = None if not selected else school_map[selected].get('logo_url')
        new_name = st.text_input("School Display Name", value=school_name)
        uploaded = st.file_uploader("Upload School Logo (PNG/JPEG)", type=["png","jpg","jpeg"]) 
        if uploaded and selected:
            # Save uploaded logo to data/logos/<school_id>.*
            import os
            out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "logos")
            os.makedirs(out_dir, exist_ok=True)
            ext = uploaded.name.split('.')[-1]
            out_path = os.path.join(out_dir, f"logo_{selected}.{ext}")
            with open(out_path, 'wb') as f:
                f.write(uploaded.getbuffer())
            # Store relative path
            rel = os.path.relpath(out_path, os.path.dirname(__file__))
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE schools SET logo_url=? WHERE school_id=?", (out_path, selected))
            st.success("Logo uploaded and saved")

        if st.button("💾 Save General Settings"):
            if selected and new_name:
                with db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("UPDATE schools SET name=? WHERE school_id=?", (new_name.strip(), selected))
                st.success("School branding updated")
            else:
                st.success("Settings saved (demo mode)!")

    with tab2:
        st.toggle("System alerts", value=True)
        st.toggle("Weekly performance digest", value=True)
        st.toggle("Fee overdue reminders", value=True)
        st.slider("Alert frequency (days)", 1, 7, 1)
        if st.button("💾 Save Notification Settings"):
            st.success("Notification settings saved (demo mode)!")
