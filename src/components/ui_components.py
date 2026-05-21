"""
UI Components - Custom CSS injection and reusable Streamlit UI widgets.
"""

import streamlit as st


def inject_custom_css():
    """Inject dark SaaS glassmorphism CSS into the Streamlit app."""
    st.markdown("""
    <style>
    /* ===== GLOBAL DARK THEME ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp {
        background: #0a0e1a !important;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1226 0%, #0a0e1a 100%) !important;
        border-right: 1px solid #1e2a45 !important;
    }

    [data-testid="stSidebar"] .stButton button {
        background: transparent !important;
        border: 1px solid #1e2a45 !important;
        color: #8892b0 !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        text-align: left !important;
        font-size: 0.9rem !important;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background: linear-gradient(135deg, #00ff8810 0%, #00b4d810 100%) !important;
        border-color: #00ff88 !important;
        color: #00ff88 !important;
        transform: translateX(4px) !important;
    }

    /* ===== METRIC CARDS ===== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #0d1226 0%, #111827 100%) !important;
        border: 1px solid #1e2a45 !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
    }

    [data-testid="stMetricLabel"] {
        color: #8892b0 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    [data-testid="stMetricValue"] {
        color: #ccd6f6 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.85rem !important;
    }

    /* ===== INPUTS ===== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTextArea textarea,
    .stNumberInput input {
        background: #0d1226 !important;
        border: 1px solid #1e2a45 !important;
        border-radius: 10px !important;
        color: #ccd6f6 !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus {
        border-color: #00ff88 !important;
        box-shadow: 0 0 0 2px rgba(0,255,136,0.15) !important;
    }

    /* ===== BUTTONS ===== */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #00ff88 0%, #00b4d8 100%) !important;
        color: #0a0e1a !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0,255,136,0.25) !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0,255,136,0.4) !important;
    }

    /* ===== DATAFRAME ===== */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid #1e2a45 !important;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: #0d1226 !important;
        border-radius: 12px !important;
        gap: 4px !important;
        padding: 4px !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #8892b0 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 8px 20px !important;
        font-weight: 500 !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00ff8820, #00b4d820) !important;
        color: #00ff88 !important;
        border-bottom: 2px solid #00ff88 !important;
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background: #0d1226 !important;
        border: 1px solid #1e2a45 !important;
        border-radius: 10px !important;
        color: #ccd6f6 !important;
    }

    /* ===== ALERTS/INFO ===== */
    .stAlert {
        border-radius: 12px !important;
        border-left-width: 4px !important;
    }

    /* ===== SPINNER ===== */
    .stSpinner > div {
        border-top-color: #00ff88 !important;
    }

    /* ===== DIVIDER ===== */
    hr {
        border-color: #1e2a45 !important;
        margin: 1rem 0 !important;
    }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0a0e1a; }
    ::-webkit-scrollbar-thumb { background: #1e2a45; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #00ff88; }

    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


def kpi_card(title: str, value: str, subtitle: str = "", icon: str = "📊",
             color: str = "#00ff88", delta: str = None):
    """Render a glassmorphism KPI card."""
    delta_html = ""
    if delta:
        delta_color = "#2ed573" if "+" in delta else "#ff4757"
        delta_html = f'<p style="color:{delta_color};font-size:0.8rem;margin:4px 0 0 0;font-weight:600;">{delta}</p>'

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0d1226 0%, #111827 100%);
        border: 1px solid #1e2a45;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease;
        margin-bottom: 1rem;
    ">
        <div style="
            position: absolute; top: 0; right: 0;
            width: 80px; height: 80px;
            background: radial-gradient(circle, {color}20 0%, transparent 70%);
            border-radius: 0 16px 0 80px;
        "></div>
        <div style="font-size: 1.8rem; margin-bottom: 8px;">{icon}</div>
        <div style="color: #8892b0; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                  letter-spacing: 0.8px; margin: 0 0 6px 0;">{title}</div>
        <div style="color: {color}; font-size: 2rem; font-weight: 800; margin: 0;
                   text-shadow: 0 0 20px {color}40;">{value}</div>
        {delta_html}
        <div style="color: #8892b0; font-size: 0.75rem; margin: 6px 0 0 0;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def alert_card(title: str, message: str, severity: str = "medium",
               student: str = "", time_str: str = ""):
    """Render an AI alert card."""
    colors = {
        "critical": ("#ff4757", "🔴"),
        "high": ("#ff6348", "🟠"),
        "medium": ("#ffa502", "🟡"),
        "low": ("#2ed573", "🟢"),
    }
    color, emoji = colors.get(severity.lower(), ("#ccd6f6", "⚪"))

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0d1226, #111827);
        border: 1px solid {color}40;
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 10px;
        box-shadow: 0 2px 12px {color}15;
    ">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
            <span style="font-size: 1.1rem;">{emoji}</span>
            <strong style="color: #ccd6f6; font-size: 0.95rem;">{title}</strong>
            <span style="margin-left: auto; color: #4a5568; font-size: 0.75rem;">{time_str}</span>
        </div>
        <p style="color: #8892b0; font-size: 0.85rem; margin: 0;">{message}</p>
        {f'<p style="color: {color}; font-size:0.8rem; margin: 6px 0 0 0; font-weight:600;">👤 {student}</p>' if student else ''}
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = "", icon: str = ""):
    """Render a styled section header with gradient text."""
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="
            background: linear-gradient(135deg, #00ff88, #00b4d8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 1.6rem;
            font-weight: 800;
            margin: 0 0 4px 0;
        ">{icon} {title}</h2>
        {f'<p style="color:#8892b0; font-size:0.9rem; margin:0;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", badge: str = ""):
    """Render a full-width page header."""
    badge_html = f'<span style="background:#00ff8820;color:#00ff88;border:1px solid #00ff8840;border-radius:20px;padding:3px 12px;font-size:0.8rem;font-weight:600;">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0d1226 0%, #111827 100%);
        border: 1px solid #1e2a45;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute; top: 0; right: 0; width: 200px; height: 100%;
            background: linear-gradient(135deg, #00ff8808, #00b4d808);
        "></div>
        <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
            <div>
                <h1 style="
                    background: linear-gradient(135deg, #ccd6f6, #a8b2d8);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-size: 1.8rem; font-weight: 800; margin: 0 0 6px 0;
                ">{title}</h1>
                {f'<p style="color:#8892b0;font-size:0.9rem;margin:0;">{subtitle}</p>' if subtitle else ''}
            </div>
            {badge_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def student_performance_badge(score: float) -> str:
    """Return HTML badge for student performance."""
    if score >= 80:
        return f'<span style="background:#00ff8820;color:#00ff88;border-radius:6px;padding:2px 8px;font-size:0.8rem;font-weight:600;">⭐ {score:.1f}%</span>'
    elif score >= 60:
        return f'<span style="background:#ffa50220;color:#ffa502;border-radius:6px;padding:2px 8px;font-size:0.8rem;font-weight:600;">📈 {score:.1f}%</span>'
    else:
        return f'<span style="background:#ff475720;color:#ff4757;border-radius:6px;padding:2px 8px;font-size:0.8rem;font-weight:600;">⚠️ {score:.1f}%</span>'


def render_sidebar_nav(nav_items: list, role_label: str, user_name: str, school_name: str = ""):
    """Render the sidebar navigation."""
    with st.sidebar:
        # User profile section
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #00ff8815, #00b4d815);
            border: 1px solid #00ff8830;
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 20px;
            text-align: center;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 8px;">🎓</div>
            <h3 style="color: #ccd6f6; margin: 0 0 4px 0; font-size: 1rem; font-weight: 700;">{user_name}</h3>
            <span style="
                background: linear-gradient(135deg, #00ff88, #00b4d8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 0.8rem; font-weight: 600;
            ">{role_label}</span>
            {f'<p style="color:#4a5568;font-size:0.75rem;margin:4px 0 0 0;">{school_name}</p>' if school_name else ''}
        </div>
        """, unsafe_allow_html=True)
        # Navigation items
        st.markdown("<div style='margin-top:12px;'>", unsafe_allow_html=True)
        for item in nav_items:
            label = item.get("label")
            page = item.get("page")
            if st.button(label, key=f"sidebar_{label}", use_container_width=True):
                st.session_state.page = page
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("Logout", key="sidebar_logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.experimental_rerun()


def render_landing_dashboard():
        """Render a modern landing dashboard with Sign In and Sign Up School buttons."""
        inject_custom_css()

        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:center;height:70vh;padding:40px 20px;">
            <div style="width:100%;max-width:1100px;">
                <div style="display:flex;gap:24px;flex-wrap:wrap;align-items:stretch;">

                    <div style="flex:1 1 380px; background: linear-gradient(135deg, rgba(13,18,38,0.8), rgba(17,24,39,0.6)); border-radius:20px; padding:28px; border:1px solid rgba(30,42,69,0.6); backdrop-filter: blur(8px);">
                        <div style="display:flex;align-items:center;gap:16px;margin-bottom:14px;">
                            <div style="font-size:2.2rem;">🎓</div>
                            <div>
                                <h1 style="margin:0;color:linear-gradient(135deg,#ccd6f6,#a8b2d8);">EduAI Platform</h1>
                                <p style="margin:6px 0 0 0;color:#8892b0;">AI-powered school intelligence — reports, analytics, and AI guidance for principals and teachers.</p>
                            </div>
                        </div>

                        <div style="margin-top:18px;">
                            <p style="color:#ccd6f6;margin:0 0 10px 0;font-weight:600;">Get started</p>
                            <p style="color:#8892b0;margin:0 0 18px 0;">Sign in to access dashboards or create a new school account to begin.</p>

                            <div style="display:flex;gap:12px;flex-wrap:wrap;">
                                <form action="" style="margin:0;padding:0;">
                                    <!-- Buttons rendered by Streamlit -->
                                </form>
                            </div>
                        </div>
                    </div>

                    <div style="flex:0 1 320px; display:flex;flex-direction:column;gap:12px;">
                        <div style="background: linear-gradient(135deg,#081022,#0b1224); padding:18px; border-radius:16px; border:1px solid rgba(30,42,69,0.6); backdrop-filter: blur(6px);">
                            <h3 style="color:#ccd6f6;margin:0 0 6px 0;">Quick Actions</h3>
                            <p style="color:#8892b0;margin:0 0 12px 0;">Sign in if you already have an account, or register your school to start.</p>
                            <div id="landing_buttons" style="display:flex;gap:10px;flex-direction:column;">
                            </div>
                        </div>
                        <div style="background: linear-gradient(135deg, rgba(0,255,136,0.03), rgba(0,180,216,0.02)); border-radius:12px; padding:12px; border:1px solid rgba(30,42,69,0.5);">
                            <p style="color:#ccd6f6;margin:0;font-size:0.9rem;">Secure · Scalable · AI-driven insights</p>
                        </div>
                    </div>

                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Buttons rendered via Streamlit for interactivity
        cols = st.columns([3,1])
        with cols[0]:
                if st.button("🔐 Sign In", key="landing_signin", use_container_width=True):
                        st.session_state.auth_mode = "signin"
                        st.rerun()
        with cols[1]:
            if st.button("✨ Sign Up School", key="landing_signup", use_container_width=True):
                # Directly open signup as principal and create school
                st.session_state.auth_mode = "signup"
                st.session_state.signup_role = "principal"
                st.session_state.creating_school = True
                st.rerun()

        # Small navigation for landing quick links
        st.markdown("**Navigation**")
        landing_nav = ["🔐 Sign In", "✨ Sign Up School"]
        for label in landing_nav:
            if st.button(label, key=f"landing_nav_{label}", use_container_width=True):
                if "Sign In" in label:
                    st.session_state.auth_mode = "signin"
                else:
                    st.session_state.auth_mode = "signup"
                    st.session_state.signup_role = "principal"
                    st.session_state.creating_school = True
                st.rerun()
                st.rerun()

        st.markdown("---")

        # Logout
        from src.auth.auth_manager import AuthManager
        AuthManager().render_logout_button()

        # Version footer
        st.markdown("""
        <div style="text-align:center; margin-top: 20px;">
            <p style="color:#4a5568; font-size:0.7rem;">EduAI Platform v1.0</p>
            <p style="color:#4a5568; font-size:0.7rem;">AI-Powered School Intelligence</p>
        </div>
        """, unsafe_allow_html=True)
