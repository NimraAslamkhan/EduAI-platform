import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, token: str, reset_link_base: str = None) -> bool:
    """Send a password reset email containing the token (and link if given).

    Required env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL
    """
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    from_email = os.environ.get("FROM_EMAIL") or smtp_user

    if not smtp_host or not smtp_user or not smtp_pass or not from_email:
        logger.warning("SMTP not configured; cannot send password reset email.")
        return False

    subject = "EduAI Password Reset"
    if reset_link_base:
        reset_link = f"{reset_link_base.rstrip('/')}/?reset_token={token}&email={to_email}"
        body = f"You requested a password reset. Click the link below to reset your password:\n\n{reset_link}\n\nIf you didn't request this, ignore this message. The link expires in 60 minutes."
    else:
        body = f"You requested a password reset. Use the token below to reset your password:\n\n{token}\n\nIf you didn't request this, ignore this message. The token expires in 60 minutes."

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Use STARTTLS if port is 587
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.ehlo()
        if smtp_port == 587:
            server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Password reset email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return False
