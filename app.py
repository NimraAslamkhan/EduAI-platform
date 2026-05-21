"""
EduAI Platform - AI-Powered School Intelligence Platform
Main Application Entry Point
"""

import streamlit as st
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="EduAI Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.database.db_manager import DatabaseManager
from src.auth.auth_manager import AuthManager
from src.components.ui_components import inject_custom_css
from src.dashboards.super_admin import render_super_admin_dashboard
from src.dashboards.principal import render_principal_dashboard
from src.dashboards.teacher import render_teacher_dashboard
from src.dashboards.parent import render_parent_dashboard


def initialize_app():
    if "db_initialized" not in st.session_state:
        try:
            db = DatabaseManager()
            db.initialize_database()
            db.seed_sample_data()
            st.session_state.db_initialized = True
            st.session_state.db = db
        except Exception as e:
            st.error(f"Failed to initialize database: {e}")
    elif "db" not in st.session_state:
        st.session_state.db = DatabaseManager()


# ─── Role cards config ────────────────────────────────────────────────────────
ROLES = [
    {
        "key": "super_admin",
        "label": "Super Admin",
        "icon": "🛡️",
        "desc": "Manage entire platform, all schools & users",
        "color": "#ff6b6b",
    },
    {
        "key": "principal",
        "label": "Principal",
        "icon": "🏫",
        "desc": "School overview, analytics & AI alerts",
        "color": "#ffa500",
    },
    {
        "key": "teacher",
        "label": "Teacher",
        "icon": "📚",
        "desc": "Student grades, attendance & predictions",
        "color": "#00b4d8",
    },
    {
        "key": "parent",
        "label": "Parent",
        "icon": "👨‍👩‍👧",
        "desc": "Track your child's progress & fees",
        "color": "#00ff88",
    },
]


def render_auth_page():
    """Render the combined Sign In / Sign Up page with role selection."""

    # ── init session flags ──
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "landing"      # 'landing' | 'signin' | 'role_select' | 'signup'
    if "signup_role" not in st.session_state:
        st.session_state.signup_role = None

    from src.components.ui_components import render_landing_dashboard
    inject_custom_css()

    if st.session_state.auth_mode == "landing":
        render_landing_dashboard()
        return

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        # ── Logo ──
        st.markdown("""
        <div style="text-align:center; padding:40px 0 10px 0;">
            <div style="font-size:3rem;">🎓</div>
            <h1 style="color:#00ff88; font-size:2.2rem; margin:0; font-weight:800; letter-spacing:-1px;">
                EduAI Platform
            </h1>
            <p style="color:#8892b0; font-size:0.95rem; margin-top:6px;">
                AI-Powered School Intelligence Platform
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Tab buttons ──
        t1, t2 = st.columns(2)
        with t1:
            sign_in_type = "primary" if st.session_state.auth_mode == "signin" else "secondary"
            if st.button("🔐 Sign In", use_container_width=True, type=sign_in_type):
                st.session_state.auth_mode = "signin"
                st.session_state.signup_role = None
                st.rerun()
        with t2:
            sign_up_type = "primary" if st.session_state.auth_mode in ("role_select", "signup") else "secondary"
            if st.button("✨ Sign Up", use_container_width=True, type=sign_up_type):
                st.session_state.auth_mode = "role_select"
                st.session_state.signup_role = None
                st.rerun()

        st.markdown("<hr style='margin:12px 0;border-color:#1e3a5f;'>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════
        # ══════════════════════════════════════════════
        #  STEP 3 — ROLE REGISTRATION
        # ══════════════════════════════════════════════
        if st.session_state.auth_mode == "role_register":
            st.markdown("### Role Registration — Add initial users for your school")
            st.caption("Register Admin, Principal, Teacher or Parent accounts tied to your school")

            user = st.session_state.get('user') or {}
            current_school_id = user.get('school_id')
            if not current_school_id:
                st.error("No school context found. Please sign up a school first.")
                if st.button("Back to Sign Up"):
                    st.session_state.auth_mode = 'signup'
                    st.rerun()
                return

            roles = [
                {"key": "super_admin", "label": "Admin", "icon": "🛡️"},
                {"key": "principal", "label": "Principal", "icon": "🏫"},
                {"key": "teacher", "label": "Teacher", "icon": "📚"},
                {"key": "parent", "label": "Parent", "icon": "👨‍👩‍👧"},
            ]

            cols = st.columns(4)
            for i, r in enumerate(roles):
                with cols[i]:
                    if st.button(f"{r['icon']} {r['label']}", key=f"rolereg_{r['key']}"):
                        st.session_state.role_register_target = r['key']
                        st.session_state.auth_mode = 'role_register_form'
                        st.rerun()

            st.markdown("---")
            st.markdown("Click a role to add a user for this school. After adding, you can add more or go to dashboard.")

        if st.session_state.auth_mode == 'role_register_form':
            target = st.session_state.get('role_register_target')
            if not target:
                st.session_state.auth_mode = 'role_register'
                st.rerun()
            role_label = next((r['label'] for r in [
                {"key": "super_admin", "label": "Admin"},
                {"key": "principal", "label": "Principal"},
                {"key": "teacher", "label": "Teacher"},
                {"key": "parent", "label": "Parent"},
            ] if r['key'] == target), target)

            st.markdown(f"### Create {role_label} for your school")
            current_school_id = st.session_state.get('user', {}).get('school_id')
            db = DatabaseManager()

            with st.form("role_create_form"):
                if target == 'parent':
                    # list students in this school
                    students = db.get_all_students(school_id=current_school_id)
                    student_options = {s['student_id']: f"{s.get('full_name','Student')} ({s.get('class_name','')})" for s in students}
                    if not student_options:
                        st.info("No students found for this school. Add students later from dashboard.")
                    student_id = st.selectbox("Student", options=list(student_options.keys()), format_func=lambda x: student_options.get(x) if x else "", index=0 if student_options else None)
                    full_name = st.text_input("Parent Full Name *")
                    email = st.text_input("Parent Email *")
                    password = st.text_input("Password *", type="password")
                    confirm = st.text_input("Confirm Password *", type="password")
                else:
                    full_name = st.text_input("Full Name *")
                    email = st.text_input("Email *")
                    password = st.text_input("Password *", type="password")
                    confirm = st.text_input("Confirm Password *", type="password")

                # show school id (read-only)
                st.markdown(f"**School ID:** `{current_school_id}`")

                submitted = st.form_submit_button(f"Create {role_label}")

                if submitted:
                    if not full_name or not email or not password:
                        st.error("Please fill in all required fields.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        # create user tied to current school
                        res = db.register_user(full_name=full_name, email=email, password=password, role=target, school_id=current_school_id)
                        if res.get('success'):
                            st.success(f"{role_label} created successfully.")
                            new_user = res.get('user') or {}
                            if target == 'parent' and student_options:
                                try:
                                    db.assign_parent_to_student(student_id=student_id, parent_user_id=new_user.get('user_id'))
                                    st.success("Parent linked to student successfully.")
                                except Exception as e:
                                    st.warning(f"Created parent but failed to link to student: {e}")

                            if st.button("Add another user"):
                                st.session_state.auth_mode = 'role_register'
                                st.rerun()
                            if st.button("Go to Dashboard"):
                                st.session_state.auth_mode = 'signin'
                                st.rerun()
                        else:
                            st.error(res.get('error', 'Failed to create user.'))
        #  SIGN IN
        # ══════════════════════════════════════════════
        if st.session_state.auth_mode == "signin":
            st.markdown("### Sign In to Your Account")
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="your@email.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("🚀 Sign In", use_container_width=True)

                if submitted:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        auth = AuthManager()
                        user = auth.authenticate(email, password)
                        if user:
                            # set session expiry (8 hours)
                            from datetime import datetime, timedelta
                            st.session_state.session_expires = (datetime.now() + timedelta(hours=8)).isoformat()
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.session_state.page = "Dashboard"
                            st.rerun()
                        else:
                            st.error("❌ Invalid email or password. Please check your credentials or Sign Up.")

            st.markdown("---")
            # Forgot password flow
            st.markdown("### Forgot your password?")
            with st.form("forgot_form"):
                fp_email = st.text_input("Enter your account email to receive reset instructions")
                fp_submit = st.form_submit_button("Send reset email", use_container_width=True)
                if fp_submit:
                    if not fp_email:
                        st.error("Please enter your email.")
                    else:
                        auth = AuthManager()
                        res = auth.send_password_reset(fp_email)
                        if not res.get("success"):
                            st.error(res.get("error", "Failed to create reset."))
                        else:
                            if res.get("warning"):
                                st.warning(res.get("warning"))
                                # For local testing, show token
                                if res.get("token"):
                                    st.code(f"Reset token: {res.get('token')}")
                            else:
                                st.success("If the email exists we sent password reset instructions.")

            st.markdown("---")
            st.markdown("#### Apply password reset token")
            with st.form("apply_reset_form"):
                ar_email = st.text_input("Email for reset")
                ar_token = st.text_input("Reset token")
                ar_new = st.text_input("New password", type="password")
                ar_confirm = st.text_input("Confirm new password", type="password")
                ar_submit = st.form_submit_button("Apply new password", use_container_width=True)
                if ar_submit:
                    if not ar_email or not ar_token or not ar_new:
                        st.error("Please complete all fields.")
                    elif ar_new != ar_confirm:
                        st.error("Passwords do not match.")
                    else:
                        auth = AuthManager()
                        r = auth.reset_password_with_token(ar_email, ar_token, ar_new)
                        if r.get("success"):
                            st.success("Password reset successfully. You may now sign in.")
                        else:
                            st.error(r.get("error", "Failed to reset password."))

        # ══════════════════════════════════════════════
        #  STEP 1 — ROLE SELECTION
        # ══════════════════════════════════════════════
        if st.session_state.auth_mode == "role_select":
            st.markdown("### 👤 Select Your Role")
            st.caption("Choose the category that best describes you to get started.")
            st.markdown("")

            for role in ROLES:
                selected = st.session_state.signup_role == role["key"]
                border_color = role["color"] if selected else "#1e3a5f"
                bg = "rgba(0,255,136,0.06)" if selected else "rgba(255,255,255,0.02)"

                st.markdown(f"""
                <div style="
                    border:2px solid {border_color};
                    border-radius:12px;
                    padding:14px 18px;
                    margin-bottom:10px;
                    background:{bg};
                    cursor:pointer;
                    transition:all 0.2s;
                ">
                    <span style="font-size:1.6rem;">{role['icon']}</span>
                    <span style="color:#ccd6f6; font-weight:700; font-size:1.05rem; margin-left:10px;">{role['label']}</span>
                    <p style="color:#8892b0; font-size:0.85rem; margin:4px 0 0 36px;">{role['desc']}</p>
                </div>
                """, unsafe_allow_html=True)

                btn_label = f"✅ Selected — Continue as {role['label']}" if selected else f"Select {role['label']}"
                btn_type = "primary" if selected else "secondary"
                if st.button(btn_label, key=f"role_{role['key']}", use_container_width=True, type=btn_type):
                    st.session_state.signup_role = role["key"]
                    st.session_state.auth_mode = "signup"
                    st.session_state.creating_school = False
                    st.rerun()

        # ══════════════════════════════════════════════
        #  STEP 2 — SIGN UP FORM
        # ══════════════════════════════════════════════
        if st.session_state.auth_mode == "signup":
            role_info = next((r for r in ROLES if r["key"] == st.session_state.signup_role), None)
            if not role_info:
                st.session_state.auth_mode = "role_select"
                st.rerun()

            # Back button
            if st.button(f"← Back to Role Selection"):
                st.session_state.auth_mode = "role_select"
                st.session_state.signup_role = None
                st.session_state.creating_school = False
                st.rerun()

            st.markdown(f"""
            <div style="
                background:rgba(255,255,255,0.03);
                border:1px solid {role_info['color']};
                border-radius:10px;
                padding:12px 18px;
                margin-bottom:16px;
            ">
                <span style="font-size:1.5rem;">{role_info['icon']}</span>
                <span style="color:{role_info['color']}; font-weight:700; font-size:1.1rem; margin-left:10px;">
                    Create {role_info['label']} Account
                </span>
            </div>
            """, unsafe_allow_html=True)

            with st.form("signup_form"):
                full_name = st.text_input("Full Name *", placeholder="e.g. Nimra Aslam")
                email = st.text_input("Email Address *", placeholder="nimra@example.com")

                # If this signup flow was opened from 'Sign Up School', show school fields
                if st.session_state.get('creating_school'):
                    school_name = st.text_input("School / Organization Name *", placeholder="e.g. Beacon House School")
                    unique_school_id = st.text_input("Unique School ID *", placeholder="e.g. greenvalley-academy")
                elif st.session_state.signup_role == "super_admin":
                    school_name = st.text_input("School / Organization Name *", placeholder="e.g. Beacon House School")
                    unique_school_id = None
                else:
                    school_name = ""
                    unique_school_id = None

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    password = st.text_input("Password *", type="password", placeholder="Min 6 characters")
                with col_p2:
                    confirm = st.text_input("Confirm Password *", type="password", placeholder="Re-enter password")

                submitted = st.form_submit_button(f"🚀 Create {role_info['label']} Account", use_container_width=True)

                if submitted:
                    errors = []
                    if not full_name.strip():
                        errors.append("Full name is required.")
                    if not email.strip():
                        errors.append("Email is required.")
                    if not password:
                        errors.append("Password is required.")
                    elif len(password) < 6:
                        errors.append("Password must be at least 6 characters.")
                    elif password != confirm:
                        errors.append("Passwords do not match.")

                    if errors:
                        for err in errors:
                            st.error(f"❌ {err}")
                    else:
                        db = DatabaseManager()
                        result = db.register_user(
                            full_name=full_name,
                            email=email,
                            password=password,
                            role=st.session_state.signup_role,
                            school_name=school_name,
                            unique_school_id=unique_school_id
                        )
                        if result["success"]:
                            st.success(f"✅ Account created! Welcome, {full_name.split()[0]}!")
                            # Log user in
                            st.session_state.logged_in = True
                            st.session_state.user = result["user"]
                            st.session_state.page = "Dashboard"
                            # If we just created a school, redirect to role registration
                            if st.session_state.get('creating_school'):
                                st.session_state.auth_mode = "role_register"
                                st.session_state.creating_school = False
                            else:
                                st.session_state.auth_mode = "signin"
                            st.session_state.signup_role = None
                            st.rerun()
                        else:
                            st.error(f"❌ {result['error']}")


def main():
    initialize_app()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if not st.session_state.logged_in:
        render_auth_page()
    else:
        # validate session expiry
        from src.auth.auth_manager import AuthManager
        auth = AuthManager()
        if not auth.ensure_session_valid():
            st.warning("Your session has expired. Please sign in again.")
            render_auth_page()
            return

        inject_custom_css()
        user = st.session_state.user
        role = user.get("role", "")

        try:
            if role == "super_admin":
                render_super_admin_dashboard()
            elif role == "principal":
                render_principal_dashboard()
            elif role == "teacher":
                render_teacher_dashboard()
            elif role == "parent":
                render_parent_dashboard()
            else:
                st.error("Unknown role. Please contact your administrator.")
                if st.button("Logout"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
        except Exception as e:
            logger.error(f"Dashboard render error: {e}", exc_info=True)
            st.error(f"⚠️ An unexpected error occurred: {e}")
            if st.button("🔄 Reload Application"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()


if __name__ == "__main__":
    main()
