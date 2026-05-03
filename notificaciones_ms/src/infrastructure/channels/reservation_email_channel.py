import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.application.dtos.reservation_confirmation_dto import ReservationConfirmationDTO
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)


async def send_reservation_confirmation_email(dto: ReservationConfirmationDTO) -> bool:
    """Sends a reservation confirmation email to the guest. Returns True on success."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("smtp_not_configured — skipping reservation confirmation email")
        return False

    subject = f"Confirmación de reserva #{dto.reservation_code}"

    body = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
    <h2 style="color:#27ae60;">Confirmación de Reserva</h2>
    <p>Estimado/a <b>{dto.guest_name}</b>,</p>
    <p>Su reserva ha sido <b>confirmada exitosamente</b>. A continuación encontrará los detalles:</p>
    <table border="1" cellpadding="10" cellspacing="0"
           style="border-collapse:collapse;width:100%;margin-bottom:20px;">
        <tr style="background:#f2f2f2;">
            <td><b>Código de reserva</b></td>
            <td>{dto.reservation_code}</td>
        </tr>
        <tr>
            <td><b>Estado</b></td>
            <td style="color:#27ae60;"><b>Confirmada</b></td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td><b>Hospedaje</b></td>
            <td>{dto.property_name}</td>
        </tr>
        <tr>
            <td><b>Dirección</b></td>
            <td>{dto.property_address}</td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td><b>Check-in</b></td>
            <td>{dto.check_in.strftime('%d/%m/%Y')}</td>
        </tr>
        <tr>
            <td><b>Check-out</b></td>
            <td>{dto.check_out.strftime('%d/%m/%Y')}</td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td><b>Número de huéspedes</b></td>
            <td>{dto.num_guests}</td>
        </tr>
        <tr>
            <td><b>Valor total pagado</b></td>
            <td><b>${dto.total_amount:,.2f}</b></td>
        </tr>
        <tr style="background:#f2f2f2;">
            <td><b>Contacto del hospedaje</b></td>
            <td>{dto.property_contact}</td>
        </tr>
    </table>
    <p>Gracias por elegir TravelHub.</p>
    <p style="color:#95a5a6;font-size:11px;">notificaciones_ms — confirmación automática</p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = dto.guest_email
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, dto.guest_email, msg.as_string())
        logger.info(
            "reservation_confirmation_email_sent reservation_code=%s guest_email=%s",
            dto.reservation_code,
            dto.guest_email,
        )
        return True
    except Exception as exc:
        logger.error(
            "reservation_confirmation_email_error reservation_code=%s error=%s",
            dto.reservation_code,
            exc,
        )
        return False
