"""
Authentication Manager - Login, session, and password hashing.
"""

import hashlib
import logging
import streamlit as st
from src.database.db_manager import DatabaseManager
from src.utils.emailer import send_password_reset_email

logger = logging.getLogger(__name__)


class AuthManager:
    """Handles user authentication and session management."""

    def __init__(self):
        self.db = DatabaseManager()

    def hash_password(self, password: str) -> str:
        """Hash password with SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, email: str, password: str) -> dict | None:
        """Authenticate user by email and password. Returns user dict or None."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email.strip().lower(),))
                row = cursor.fetchone()
                if not row:
                    return None
                user = dict(row)
                stored_hash = user.get('password_hash')
                if self.db.verify_password(stored_hash, password):
                    # load school name for returned user dict
                    cursor.execute("SELECT name as school_name FROM schools WHERE school_id = ?", (user.get('school_id'),))
                    srow = cursor.fetchone()
                    if srow:
                        user['school_name'] = srow['school_name']
                    return user
                return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def logout(self):
        """Clear session state to log out user."""
        keys_to_clear = ["logged_in", "user", "page", "chat_history"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

    def ensure_session_valid(self) -> bool:
        """Check session expiry and clear session if expired. Returns True if still valid."""
        from datetime import datetime
        expires = st.session_state.get('session_expires')
        if not expires:
            return True
        try:
            if isinstance(expires, str):
                expires_dt = datetime.fromisoformat(expires)
            else:
                expires_dt = expires
            if datetime.now() > expires_dt:
                self.logout()
                return False
            return True
        except Exception:
            return True

    def send_password_reset(self, email: str) -> dict:
        """Create reset token and send email. Returns dict with success/error."""
        try:
            result = self.db.create_password_reset(email)
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "Failed to create reset")}

            token = result.get("token")
            # Attempt to send email; if SMTP not configured, result may be False
            sent = send_password_reset_email(email, token)
            if not sent:
                # Still return success but warn that email wasn't sent (caller can surface message)
                return {"success": True, "warning": "Email not sent (SMTP not configured). Use token provided by the system for testing.", "token": token}
            return {"success": True}
        except Exception as e:
            logger.error(f"send_password_reset error: {e}")
            return {"success": False, "error": str(e)}

    def reset_password_with_token(self, email: str, token: str, new_password: str) -> dict:
        """Consume a reset token and set a new password."""
        try:
            if not token or not email or not new_password:
                return {"success": False, "error": "Missing parameters."}
            if len(new_password) < 6:
                return {"success": False, "error": "Password must be at least 6 characters."}
            result = self.db.consume_password_reset(email, token, new_password)
            return result
        except Exception as e:
            logger.error(f"reset_password_with_token error: {e}")
            return {"success": False, "error": str(e)}

    def get_current_user(self) -> dict | None:
        """Return the currently logged-in user."""
        return st.session_state.get("user")

    def require_role(self, allowed_roles: list) -> bool:
        """Check if current user has one of the allowed roles."""
        user = self.get_current_user()
        if not user:
            return False
        return user.get("role") in allowed_roles

    def render_logout_button(self, sidebar: bool = True):
        """Render a styled logout button."""
        container = st.sidebar if sidebar else st
        if container.button("🚪 Logout", use_container_width=True, type="secondary"):
            self.logout()
            st.rerun()
