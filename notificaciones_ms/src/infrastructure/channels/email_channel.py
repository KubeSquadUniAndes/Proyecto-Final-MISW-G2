import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.application.dtos.notification_dto import SendNotificationDTO
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

SEVERITY_COLOR = {
    "low": "#f39c12",
    "medium": "#e67e22",
    "high": "#c0392b",
}


async def send_email(dto: SendNotificationDTO) -> bool:
    """Sends a security alert email via SMTP. Returns True on success."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("smtp_not_configured — skipping email")
        return False

    color = SEVERITY_COLOR.get(dto.severity, "#7f8c8d")
    subject = f"[SECURITY ALERT] {dto.severity.upper()} anomaly — user {dto.user_id}"

    body = f"""
    <html><body style="font-family:Arial,sans-serif;">
    <h2 style="color:{color};">🚨 Security Alert — Anomalous Booking Detected</h2>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
        <tr><td><b>User ID</b></td><td>{dto.user_id}</td></tr>
        <tr><td><b>Booking ID</b></td><td>{dto.booking_id}</td></tr>
        <tr><td><b>Anomaly Type</b></td><td>{dto.anomaly_type}</td></tr>
        <tr><td><b>Severity</b></td><td style="color:{color};"><b>{dto.severity.upper()}</b></td></tr>
        <tr><td><b>Score</b></td><td>{dto.score:.2f} / 1.00</td></tr>
        <tr><td><b>Description</b></td><td>{dto.description}</td></tr>
        <tr><td><b>Detected At</b></td><td>{dto.detected_at.isoformat()}</td></tr>
    </table>
    <p>The user has been <b>blocked</b> and all active sessions have been revoked.</p>
    <p style="color:#95a5a6;font-size:11px;">notificaciones_ms — automated security alert</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = settings.EMAIL_TO
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, settings.EMAIL_TO, msg.as_string())
        logger.info("email_sent user_id=%s", dto.user_id)
        return True
    except Exception as exc:
        logger.error("email_error user_id=%s error=%s", dto.user_id, exc)
        return False
