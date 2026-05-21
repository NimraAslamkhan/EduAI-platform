"""
Principal / Management Dashboard - Full school overview with AI analytics.
"""

import streamlit as st
import pandas as pd
from src.database.db_manager import DatabaseManager
from src.components.ui_components import (
    kpi_card, section_header, page_header, render_sidebar_nav, alert_card
)
from src.analytics.analytics_engine import (
    attendance_trend_chart, grade_distribution_chart, class_comparison_chart,
    subject_performance_chart, risk_scatter_chart, fee_collection_chart, heatmap_attendance
)
from src.utils.helpers import grade_from_score, risk_level, format_currency, time_ago


def render_principal_dashboard():
    """Render the full Principal dashboard."""
    user = st.session_state.user
    db = DatabaseManager()

    nav_items = [
        {"label": "🏠 Dashboard", "page": "Dashboard"},
        {"label": "🏛️ School Report", "page": "School Report"},
        {"label": "👨‍🎓 Students", "page": "Students"},
        {"label": "👩‍🏫 Teachers", "page": "Teachers"},
        {"label": "📊 Analytics", "page": "Analytics"},
        {"label": "🤖 AI Assistant", "page": "AI Assistant"},
        {"label": "📅 Attendance", "page": "Attendance"},
        {"label": "💰 Fees", "page": "Fees"},
        {"label": "🔔 Alerts", "page": "Alerts"},
        {"label": "⚙️ Settings", "page": "Settings"},
    ]

    render_sidebar_nav(
        nav_items,
        role_label="Principal",
        user_name=user["full_name"],
        school_name=user.get("school_name", "Green Valley Academy"),
    )

    page = st.session_state.get("page", "Dashboard")

    if page == "Dashboard":
        _render_overview(db, user)
    elif page == "School Report":
        _render_school_report(db, user)
    elif page == "Students":
        _render_students(db, user)
    elif page == "Teachers":
        _render_teachers(db)
    elif page == "Analytics":
        _render_analytics(db)
    elif page == "AI Assistant":
        _render_ai_assistant(db)
    elif page == "Attendance":
        _render_attendance(db)
    elif page == "Fees":
        _render_fees(db)
    elif page == "Alerts":
        from src.alerts.alert_system import render_alerts_page
        render_alerts_page(school_id=1)
    elif page == "Settings":
        _render_settings(user)


def _render_overview(db: DatabaseManager, user: dict):
    page_header(
        "Principal Dashboard",
        "Real-time school intelligence & AI insights",
        badge="🟢 Live"
    )

    stats = db.get_school_summary(school_id=1)

    # KPI Row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        kpi_card("Total Students", str(stats["total_students"]), "Active enrollments", "👨‍🎓", "#00ff88")
    with c2:
        kpi_card("Total Teachers", str(stats["total_teachers"]), "Staff members", "👩‍🏫", "#00b4d8")
    with c3:
        kpi_card("Attendance Rate", f"{stats['attendance_rate']}%", "Last 30 days", "📅",
                 "#00ff88" if stats["attendance_rate"] >= 80 else "#ffa502")
    with c4:
        kpi_card("Average Score", f"{stats['avg_marks']}%", "All subjects", "📊",
                 "#00ff88" if stats["avg_marks"] >= 65 else "#ff6348")
    with c5:
        kpi_card("Active Alerts", str(stats["active_alerts"]), "Requires attention", "🔔",
                 "#ff4757" if stats["active_alerts"] > 5 else "#ffa502")
    with c6:
        kpi_card("Classes", str(stats["total_classes"]), "Total classes", "🏫", "#7b5ea7")

    st.markdown("---")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        section_header("Attendance Trend", "Last 30 days", "📅")
        trend_data = db.get_attendance_trend(school_id=1, days=30)
        st.plotly_chart(attendance_trend_chart(trend_data), use_container_width=True)

        section_header("Class Attendance Comparison", "", "🏫")
        class_att = db.get_class_attendance_summary(school_id=1, days=30)
        st.plotly_chart(class_comparison_chart(class_att), use_container_width=True)

    with col_right:
        section_header("Active AI Alerts", "", "🔔")
        alerts = db.get_ai_alerts(school_id=school_id, resolved=False)
        if alerts:
            for alert in alerts[:5]:
                alert_card(
                    title=alert["title"],
                    message=alert["message"][:80] + "...",
                    severity=alert["severity"],
                    student=alert.get("student_name", ""),
                    time_str=time_ago(alert["created_at"]) if alert.get("created_at") else "",
                )
            if len(alerts) > 5:
                st.caption(f"+ {len(alerts)-5} more alerts. Go to Alerts page.")
        else:
            st.success("✅ No active alerts!")

        st.markdown("---")
        # School notifications
        section_header("Announcements & Notifications", "School-wide updates", "🔔")
        notifs = db.get_notifications_for_role(school_id=school_id, role='principal', limit=10)
        if notifs:
            for notif in notifs:
                alert_card(title=notif['title'], message=notif['message'], severity='medium', time_str=time_ago(notif.get('created_at')))
        else:
            st.info("No school notifications.")
        section_header("Top Students", "", "⭐")
        top = db.get_top_students(school_id=1, limit=5)
        for i, s in enumerate(top):
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:8px;
                        border-bottom:1px solid #1e2a45;">
                <span style="color:#00ff88;font-weight:700;min-width:20px;">{i+1}</span>
                <div style="flex:1">
                    <p style="color:#ccd6f6;margin:0;font-size:0.85rem;font-weight:600;">{s['full_name']}</p>
                    <p style="color:#8892b0;margin:0;font-size:0.75rem;">{s.get('class_name','')} {s.get('section','')}</p>
                </div>
                <span style="background:#00ff8820;color:#00ff88;border-radius:6px;padding:2px 8px;font-size:0.8rem;font-weight:700;">{s['avg_score']}%</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    section_header("Risk Analysis", "Attendance vs Performance scatter", "🎯")
    ml_data = db.get_performance_data_for_ml(school_id=1)
    st.plotly_chart(risk_scatter_chart(ml_data), use_container_width=True)


def _render_students(db: DatabaseManager, user: dict):
    page_header("Student Management", "View, add, edit, and analyze student records", "👨‍🎓")

    tab1, tab2, tab3 = st.tabs(["📋 All Students", "➕ Add Student", "🎯 Risk Analysis"])

    with tab1:
        students = db.get_all_students(school_id=1)
        if not students:
            st.info("No students found.")
            return

        # Normalize student records to ensure expected fields exist
        for i, s in enumerate(students):
            if "full_name" not in s or not s.get("full_name"):
                # Fallback to other possible name fields
                s["full_name"] = s.get("name") or s.get("student_name") or f"Student {s.get('student_id', i)}"

        # Filter controls
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search = st.text_input("🔍 Search students...", placeholder="Name or class")
        with col2:
            classes = db.get_all_classes(school_id=1)
            class_names = ["All Classes"] + [f"{c['class_name']} {c['section']}" for c in classes]
            selected_class = st.selectbox("Filter by Class", class_names)
        with col3:
            sort_by = st.selectbox("Sort by", ["Name", "Class", "Performance"])

        df = pd.DataFrame(students)
        df["class_label"] = df["class_name"].fillna("") + " " + df["section"].fillna("")

        if search:
            df = df[df["full_name"].str.contains(search, case=False, na=False)]
        if selected_class != "All Classes":
            df = df[df["class_label"].str.strip() == selected_class]

        # Add avg score column
        avg_scores = {}
        for _, row in df.iterrows():
            marks = db.get_student_marks(row["student_id"])
            if marks:
                avg_scores[row["student_id"]] = round(sum(m["percentage"] for m in marks) / len(marks), 1)
            else:
                avg_scores[row["student_id"]] = None

        df["avg_score"] = df["student_id"].map(avg_scores)
        df["grade"] = df["avg_score"].apply(lambda x: grade_from_score(x) if x is not None else "N/A")
        df["risk"] = df.apply(lambda r: risk_level(
            r["avg_score"] or 60,
            db.get_attendance_rate(r["student_id"], 30)
        ), axis=1)

        display_df = df[["full_name", "class_label", "gender", "age", "avg_score", "grade", "risk"]].rename(columns={
            "full_name": "Name", "class_label": "Class", "gender": "Gender",
            "age": "Age", "avg_score": "Avg Score", "grade": "Grade", "risk": "Risk Level"
        })

        st.dataframe(display_df, use_container_width=True, height=400)
        st.caption(f"Showing {len(display_df)} students")

        # Individual student view
        st.markdown("---")
        section_header("Student Profile", "Select a student for detailed analysis", "👤")
        student_names = {s.get("student_id"): s.get("full_name", f"Student {s.get('student_id')}") for s in students}
        selected_id = st.selectbox("Select Student", options=list(student_names.keys()),
                                    format_func=lambda x: student_names[x])
        if selected_id:
            _render_student_profile(db, selected_id)

    with tab2:
        _render_add_student(db)

    with tab3:
        _render_risk_analysis(db)


def _render_student_profile(db: DatabaseManager, student_id: int):
    student = db.get_student_by_id(student_id)
    if not student:
        return

    marks = db.get_student_marks(student_id)
    att_rate = db.get_attendance_rate(student_id, 30)
    avg_score = round(sum(m["percentage"] for m in marks) / len(marks), 1) if marks else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Average Score", f"{avg_score}%", "All subjects all exams", "📊",
                 "#00ff88" if avg_score >= 65 else "#ff4757")
    with col2:
        kpi_card("Attendance", f"{att_rate}%", "Last 30 days", "📅",
                 "#00ff88" if att_rate >= 80 else "#ffa502")
    with col3:
        rl = risk_level(avg_score, att_rate)
        risk_colors = {"🔴 Critical": "#ff4757", "🟠 High": "#ff6348",
                       "🟡 Medium": "#ffa502", "🟢 Low": "#00ff88"}
        kpi_card("Risk Level", rl, f"Study hours: {student.get('study_hours', 'N/A')}h/day",
                 "⚠️", risk_colors.get(rl, "#ccd6f6"))

    col_marks, col_trend = st.columns(2)
    with col_marks:
        from src.analytics.analytics_engine import student_marks_bar
        if marks:
            st.plotly_chart(student_marks_bar(marks, student["full_name"]), use_container_width=True)

    with col_trend:
        from src.analytics.analytics_engine import performance_trend_chart
        if marks:
            st.plotly_chart(performance_trend_chart(marks, student["full_name"]), use_container_width=True)

    # AI Analysis
    with st.expander("🤖 AI Analysis & Recommendations", expanded=False):
        if avg_score < 50:
            st.error(f"**⚠️ High Academic Risk** — {student['full_name']} is at risk of failing. Immediate intervention needed.")
        elif avg_score < 65:
            st.warning(f"**📈 Needs Improvement** — Performance is below average. Additional support recommended.")
        else:
            st.success(f"**✅ Performing Well** — {student['full_name']} is on track.")

        if att_rate < 75:
            st.error(f"**🚨 Attendance Issue** — {att_rate:.1f}% attendance is critically low.")

        st.markdown("**Recommendations:**")
        if avg_score < 55:
            st.markdown("- 📚 Enroll in remediation program for weakest subjects")
            st.markdown("- 👨‍🏫 Assign personal academic mentor")
        if att_rate < 80:
            st.markdown("- 📞 Schedule parent-teacher conference")
            st.markdown("- 🗓️ Create attendance improvement plan")
        if (student.get("study_hours") or 3) < 3:
            st.markdown("- ⏰ Encourage increasing daily study hours to 4+")

    # Edit student
    with st.expander("✏️ Edit Student Details", expanded=False):
        with st.form(f"edit_student_{student_id}"):
            new_name = st.text_input("Full Name", value=student.get("full_name", ""))
            col_a, col_b = st.columns(2)
            with col_a:
                new_age = st.number_input("Age", min_value=5, max_value=25,
                                           value=int(student.get("age") or 14))
            with col_b:
                new_hours = st.number_input("Study Hours/Day", min_value=0.5, max_value=12.0,
                                             value=float(student.get("study_hours") or 3.0), step=0.5)
            if st.form_submit_button("💾 Save Changes"):
                db.update_student(student_id, full_name=new_name, age=new_age, study_hours=new_hours)
                st.success("Student updated!")
                st.rerun()


def _render_add_student(db: DatabaseManager):
    section_header("Add New Student", "", "➕")
    classes = db.get_all_classes(school_id=1)

    with st.form("add_student_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name *")
            age = st.number_input("Age", min_value=5, max_value=25, value=14)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        with col2:
            class_map = {f"{c['class_name']} {c['section']}": c["class_id"] for c in classes}
            selected_class_name = st.selectbox("Class", list(class_map.keys()))
            study_hours = st.number_input("Study Hours/Day", min_value=0.5, max_value=12.0, value=3.0, step=0.5)
            phone = st.text_input("Phone", placeholder="+1-555-XXXX")

        address = st.text_area("Address", placeholder="Student's home address")

        if st.form_submit_button("➕ Add Student", use_container_width=True):
            if not full_name:
                st.error("Full name is required!")
            else:
                class_id = class_map.get(selected_class_name, classes[0]["class_id"] if classes else 1)
                new_id = db.add_student(
                    school_id=1, class_id=class_id, parent_id=None,
                    full_name=full_name, age=age, gender=gender,
                    address=address, phone=phone, study_hours=study_hours
                )
                st.success(f"✅ Student '{full_name}' added successfully! (ID: {new_id})")
                st.rerun()


def _render_risk_analysis(db: DatabaseManager):
    section_header("Dropout Risk Analysis", "AI-powered risk assessment for all students", "🎯")

    ml_data = db.get_performance_data_for_ml(school_id=1)
    if not ml_data:
        st.info("Not enough data for risk analysis.")
        return

    from src.ml.ml_pipeline import StudentMLPipeline
    pipeline = StudentMLPipeline()

    with st.spinner("Running AI predictions..."):
        if not pipeline.is_trained:
            metrics = pipeline.train(ml_data)
            if "error" not in metrics:
                st.success(f"🤖 Model trained! Performance accuracy: {metrics.get('performance_accuracy', 'N/A')}%")

        predictions = pipeline.predict_bulk(ml_data)

    df = pd.DataFrame(predictions)

    # Summary metrics
    high_risk = df[df["dropout_risk"] == "High"].shape[0]
    medium_risk = df[df["dropout_risk"] == "Medium"].shape[0]
    low_risk = df[df["dropout_risk"] == "Low"].shape[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("High Risk", str(high_risk), "Immediate intervention", "🔴", "#ff4757")
    with c2:
        kpi_card("Medium Risk", str(medium_risk), "Monitor closely", "🟡", "#ffa502")
    with c3:
        kpi_card("Low Risk", str(low_risk), "On track", "🟢", "#00ff88")

    # Scatter chart
    st.plotly_chart(risk_scatter_chart(ml_data), use_container_width=True)

    # Feature importance
    importance = pipeline.get_feature_importance()
    if importance:
        st.markdown("**🧠 Key Factors Affecting Student Performance:**")
        for feature, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            st.markdown(f"- **{feature}**: {imp:.1f}% importance")

    # Risk table
    risk_display = df[["full_name", "class_name", "avg_score", "attendance_rate",
                        "study_hours", "dropout_risk", "risk_score"]].rename(columns={
        "full_name": "Name", "class_name": "Class", "avg_score": "Avg Score (%)",
        "attendance_rate": "Attendance (%)", "study_hours": "Study Hrs",
        "dropout_risk": "Risk Level", "risk_score": "Risk Score"
    })

    # Sort by risk score desc
    risk_display = risk_display.sort_values("Risk Score", ascending=False)
    st.dataframe(risk_display, use_container_width=True, height=350)


def _render_school_report(db: DatabaseManager, user: dict):
    """Detailed school report for principals: class-wise, teacher performance, monthly trends."""
    page_header("School Report", "Class-level summaries, teacher metrics & monthly trends", "🏛️")

    school_id = user.get("school_id", 1)

    # Class summaries
    classes = db.get_all_classes(school_id=school_id)
    class_att = {r['class_label']: r['attendance_rate'] for r in db.get_class_attendance_summary(school_id=school_id, days=30)}

    class_rows = []
    for c in classes:
        cid = c.get('class_id')
        label = f"{c.get('class_name','')} {c.get('section','')}"
        students = c.get('student_count', 0)
        # class average from marks
        marks_summary = db.get_class_marks_summary(cid)
        if marks_summary:
            # average of subject averages
            class_avg = round(sum(marks_summary.values()) / max(len(marks_summary), 1), 1)
        else:
            class_avg = 0.0

        attendance_rate = class_att.get(label, 0.0)
        teacher_name = c.get('teacher_name') or 'N/A'
        class_rows.append({
            'Class': label,
            'Teacher': teacher_name,
            'Students': students,
            'Avg Score': class_avg,
            'Attendance %': attendance_rate,
        })

    import pandas as pd
    df_classes = pd.DataFrame(class_rows)

    st.subheader("Class Overview")
    st.dataframe(df_classes.sort_values(['Avg Score'], ascending=False), use_container_width=True, height=300)

    # Charts: class avg score and attendance
    import plotly.graph_objects as go
    fig1 = go.Figure(go.Bar(x=df_classes['Class'], y=df_classes['Avg Score'], marker=dict(color='#00b4d8')))
    fig1.update_layout(title='Class Average Scores', height=300, xaxis_tickangle=-45)

    fig2 = go.Figure(go.Bar(x=df_classes['Class'], y=df_classes['Attendance %'], marker=dict(color='#00ff88')))
    fig2.update_layout(title='Class Attendance (Last 30 days)', height=300, xaxis_tickangle=-45, yaxis=dict(ticksuffix='%'))

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # Teacher performance summary
    st.subheader("Teacher Performance")
    teachers = db.get_all_teachers(school_id=school_id)
    teacher_rows = []
    for t in teachers:
        tid = t.get('user_id')
        tname = t.get('full_name')
        # Compute average across classes they teach
        # find classes taught by this teacher
        teacher_classes = [c for c in classes if c.get('teacher_name') == tname]
        avgs = []
        for tc in teacher_classes:
            ms = db.get_class_marks_summary(tc.get('class_id'))
            if ms:
                avgs.append(sum(ms.values()) / max(len(ms), 1))
        teacher_avg = round(sum(avgs) / max(len(avgs), 1), 1) if avgs else None
        teacher_rows.append({'Teacher': tname, 'Classes': len(teacher_classes), 'Avg Score': teacher_avg})

    df_teachers = pd.DataFrame(teacher_rows)
    st.dataframe(df_teachers.sort_values('Avg Score', ascending=False), use_container_width=True, height=250)

    st.markdown("---")

    # Monthly trends (attendance & avg marks) last 12 months
    st.subheader("Monthly Trends (last 12 months)")
    # attendance daily -> aggregate by month
    att_daily = db.get_attendance_trend(school_id=school_id, days=365)
    att_df = pd.DataFrame(att_daily)
    if not att_df.empty:
        att_df['month'] = pd.to_datetime(att_df['date']).dt.to_period('M')
        att_month = att_df.groupby('month')['rate'].mean().reset_index()
        att_month['month'] = att_month['month'].dt.strftime('%Y-%m')
    else:
        att_month = pd.DataFrame(columns=['month', 'rate'])

    # marks over time: query marks by exam_date
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.percentage, m.exam_date
            FROM marks m
            JOIN students s ON m.student_id = s.student_id
            WHERE s.school_id = ? AND m.exam_date >= date('now','-12 months')
        """, (school_id,))
        marks_rows = cursor.fetchall()
    marks_df = pd.DataFrame([dict(r) for r in marks_rows]) if marks_rows else pd.DataFrame()
    if not marks_df.empty:
        marks_df['month'] = pd.to_datetime(marks_df['exam_date']).dt.to_period('M')
        marks_month = marks_df.groupby('month')['percentage'].mean().reset_index()
        marks_month['month'] = marks_month['month'].dt.strftime('%Y-%m')
    else:
        marks_month = pd.DataFrame(columns=['month', 'percentage'])

    # Merge months
    merged = pd.merge(att_month, marks_month, left_on='month', right_on='month', how='outer').fillna(0)
    merged = merged.sort_values('month')

    figm = go.Figure()
    figm.add_trace(go.Scatter(x=merged['month'], y=merged['rate'], name='Attendance %', mode='lines+markers', line=dict(color='#00ff88')))
    figm.add_trace(go.Scatter(x=merged['month'], y=merged.get('percentage', []), name='Avg Marks', mode='lines+markers', line=dict(color='#00b4d8')))
    figm.update_layout(title='Monthly Attendance vs Avg Marks', xaxis_tickangle=-45, height=360, yaxis=dict(range=[0, 105]))
    st.plotly_chart(figm, use_container_width=True)

    st.markdown("---")

    # Financial analytics: monthly & yearly expenses, salary status
    st.subheader("Financial Analytics")
    # Monthly expenses (last 12 months)
    monthly_exp = db.get_monthly_expenses(school_id=school_id, months=12)
    import plotly.graph_objects as go
    import pandas as pd
    if monthly_exp:
        me_df = pd.DataFrame(monthly_exp)
        # ensure sorted by month
        me_df = me_df.sort_values('month')
        fig_exp = go.Figure(go.Bar(x=me_df['month'], y=me_df['total'], marker=dict(color='#ff7b7b')))
        fig_exp.update_layout(title='Monthly Expenses (last 12 months)', height=320, xaxis_tickangle=-45)
        st.plotly_chart(fig_exp, use_container_width=True)
    else:
        st.info("No expense records available.")

    # Yearly expenses
    yearly_exp = db.get_yearly_expenses(school_id=school_id, years=3)
    if yearly_exp:
        ye_df = pd.DataFrame(yearly_exp)
        fig_y = go.Figure(go.Bar(x=ye_df['year'].astype(str), y=ye_df['total'], marker=dict(color='#7b5ea7')))
        fig_y.update_layout(title='Yearly Expenses', height=300)
        st.plotly_chart(fig_y, use_container_width=True)

    # Teacher salary status
    st.subheader("Teacher Salary Status")
    salary_rows = db.get_salary_status(school_id=school_id)
    if salary_rows:
        sf = pd.DataFrame(salary_rows)
        # highlight unpaid
        sf_display = sf[['full_name','month','year','amount','paid_amount','status','paid_date']]
        st.dataframe(sf_display.sort_values(['year','month'], ascending=False), use_container_width=True, height=280)
    else:
        st.info("No salary records found.")

    st.markdown("---")

    # AI Assistant quick access
    from src.chatbot.groq_chatbot import render_chatbot_ui
    section_header("AI Assistant & Recommendations", "Ask for suggestions or strategy for next term", "🤖")
    stats = db.get_school_summary(school_id=school_id)
    render_chatbot_ui(context={"school_info": {"school_name": user.get('school_name')}, "stats": stats})


def _render_teachers(db: DatabaseManager):
    page_header("Teachers", "Manage and monitor teaching staff", "👩‍🏫")
    teachers = db.get_all_teachers(school_id=1)

    if not teachers:
        st.info("No teachers found.")
        return

    kpi_card("Total Teachers", str(len(teachers)), "Active staff", "👩‍🏫", "#00b4d8")

    df = pd.DataFrame(teachers)
    display_df = df[["full_name", "email", "subject_expertise", "qualification",
                      "experience_years", "hire_date"]].rename(columns={
        "full_name": "Name", "email": "Email",
        "subject_expertise": "Subject", "qualification": "Qualification",
        "experience_years": "Experience (yrs)", "hire_date": "Hire Date",
    })
    st.dataframe(display_df, use_container_width=True, height=400)


def _render_analytics(db: DatabaseManager):
    page_header("School Analytics", "Comprehensive data-driven insights", "📊")

    tab1, tab2, tab3 = st.tabs(["📊 Performance", "📅 Attendance", "📚 Subjects"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            ml_data = db.get_performance_data_for_ml(school_id=1)
            marks_for_dist = [{"percentage": d["avg_score"]} for d in ml_data if d.get("avg_score")]
            st.plotly_chart(grade_distribution_chart(marks_for_dist), use_container_width=True)
        with col2:
            st.plotly_chart(risk_scatter_chart(ml_data), use_container_width=True)

        weak_students = db.get_weak_students(school_id=1, threshold=50)
        section_header(f"Weak Students ({len(weak_students)})", "Below 50% average", "⚠️")
        if weak_students:
            df_weak = pd.DataFrame(weak_students)[["full_name", "class_name", "section", "avg_score"]]
            df_weak.columns = ["Name", "Class", "Section", "Avg Score (%)"]
            st.dataframe(df_weak, use_container_width=True)

    with tab2:
        trend = db.get_attendance_trend(school_id=1, days=30)
        st.plotly_chart(attendance_trend_chart(trend), use_container_width=True)
        class_att = db.get_class_attendance_summary(school_id=1, days=30)
        st.plotly_chart(heatmap_attendance(class_att), use_container_width=True)

    with tab3:
        subj_data = db.get_subject_performance(school_id=1)
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(subject_performance_chart(subj_data), use_container_width=True)
        with col2:
            if subj_data:
                df_subj = pd.DataFrame(subj_data)[["subject_name", "avg_score", "failing_count"]]
                df_subj.columns = ["Subject", "Avg Score (%)", "Failing Students"]
                st.dataframe(df_subj, use_container_width=True)


def _render_ai_assistant(db: DatabaseManager):
    stats = db.get_school_summary(school_id=1)
    user = st.session_state.user
    context = {
        "school_info": {"school_name": user.get("school_name", "Green Valley Academy")},
        "stats": stats,
    }
    from src.chatbot.groq_chatbot import render_chatbot_ui
    render_chatbot_ui(context)


def _render_attendance(db: DatabaseManager):
    page_header("Attendance Management", "Track and analyze school-wide attendance", "📅")

    col1, col2 = st.columns(2)
    with col1:
        trend = db.get_attendance_trend(school_id=1, days=30)
        st.plotly_chart(attendance_trend_chart(trend), use_container_width=True)
    with col2:
        class_att = db.get_class_attendance_summary(school_id=1, days=30)
        st.plotly_chart(class_comparison_chart(class_att), use_container_width=True)

    section_header("Class-wise Attendance Summary", "", "📋")
    if class_att:
        df = pd.DataFrame(class_att)
        df["Status"] = df["attendance_rate"].apply(
            lambda r: "✅ Good" if r >= 80 else "⚠️ Warning" if r >= 65 else "🔴 Critical"
        )
        df.columns = ["Class", "Total Records", "Present Count", "Attendance Rate (%)", "Status"]
        st.dataframe(df, use_container_width=True)


def _render_fees(db: DatabaseManager):
    page_header("Fee Management", "Track fee collection and outstanding dues", "💰")

    fee_data = db.get_fee_summary(school_id=1)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Expected", format_currency(fee_data.get("total_expected") or 0),
                 "Entire school", "💵", "#00ff88")
    with c2:
        kpi_card("Collected", format_currency(fee_data.get("total_collected") or 0),
                 "Received", "✅", "#00b4d8")
    with c3:
        kpi_card("Pending", format_currency(fee_data.get("total_pending") or 0),
                 "Outstanding", "⏳", "#ff4757")
    with c4:
        total = fee_data.get("total_expected") or 1
        collected = fee_data.get("total_collected") or 0
        rate = round((collected / total) * 100, 1)
        kpi_card("Collection Rate", f"{rate}%", "Of expected total", "📊",
                 "#00ff88" if rate >= 80 else "#ffa502")

    st.plotly_chart(fee_collection_chart(fee_data), use_container_width=True)


def _render_settings(user: dict):
    page_header("Settings", "School and account configuration", "⚙️")

    with st.expander("👤 Account Settings", expanded=True):
        st.text_input("Full Name", value=user.get("full_name", ""), disabled=True)
        st.text_input("Email", value=user.get("email", ""), disabled=True)
        st.text_input("Role", value="Principal / Management", disabled=True)
        st.text_input("School", value=user.get("school_name", "Green Valley Academy"), disabled=True)

    with st.expander("🔔 Notification Settings"):
        st.toggle("Email notifications for new AI alerts", value=True)
        st.toggle("Weekly performance report", value=True)
        st.toggle("Attendance threshold alerts", value=True)
        st.slider("Attendance alert threshold (%)", 50, 90, 75)
        st.slider("Performance alert threshold (%)", 30, 70, 50)
        if st.button("💾 Save Notification Settings"):
            st.success("Settings saved (demo mode)!")
