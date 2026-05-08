import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.application.dtos.hotel_booking_notification_dto import (
    HotelBookingNotificationDTO,
)
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


async def send_hotel_booking_email(dto: HotelBookingNotificationDTO) -> bool:
    """Sends a new booking notification email to the hotel. Returns True on success."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "smtp_not_configured — skipping hotel booking notification email"
        )
        return False

    subject = f"Nueva reserva pendiente — {dto.booking_code}"

    body = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
    <h2 style="color:#155dfc;">Nueva Reserva Pendiente de Confirmación</h2>
    <p>Hola <b>{dto.hotel_name}</b>,</p>
    <p>Un viajero ha realizado una nueva reserva en tu hospedaje. Revisa los detalles y confirma o rechaza la solicitud.</p>
    <table border="1" cellpadding="10" cellspacing="0"
           style="border-collapse:collapse;width:100%;margin-bottom:20px;">
        <tr style="background:#f2f2f2;">
            <td><b>Código de reserva</b></td>
            <td>{dto.booking_code}</td>
        </tr>
        <tr>
            <td><b>Estado</b></td>
            <td style="color:#a66f00;"><b>Pendiente de confirmación</b></td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td><b>Huésped</b></td>
            <td>{dto.guest_name}</td>
        </tr>
        <tr>
            <td><b>Tipo de habitación</b></td>
            <td>{dto.room_type}</td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td><b>Check-in</b></td>
            <td>{dto.check_in.strftime("%d/%m/%Y")}</td>
        </tr>
        <tr>
            <td><b>Check-out</b></td>
            <td>{dto.check_out.strftime("%d/%m/%Y")}</td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td><b>Número de huéspedes</b></td>
            <td>{dto.num_guests}</td>
        </tr>
        <tr>
            <td><b>Valor total</b></td>
            <td><b>${dto.total_amount:,.2f}</b></td>
        </tr>
    </table>
    <p style="text-align:center;">
        <a href="{dto.dashboard_url}" style="display:inline-block;padding:14px 32px;background:#155dfc;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold;">
            Ver solicitudes de reserva
        </a>
    </p>
    <p style="color:#95a5a6;font-size:11px;">notificaciones_ms — notificación automática</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = dto.hotel_email
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, dto.hotel_email, msg.as_string())
        logger.info(
            "hotel_booking_email_sent booking_code=%s hotel_email=%s",
            dto.booking_code,
            dto.hotel_email,
        )
        return True
    except Exception as exc:
        logger.error(
            "hotel_booking_email_error booking_code=%s error=%s",
            dto.booking_code,
            exc,
        )
        return False
