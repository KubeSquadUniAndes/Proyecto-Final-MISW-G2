"""Email channel: sends QR check-in email with PNG + PDF attachments."""

import base64
import io
import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.application.dtos.qr_checkin_email_dto import (
    QrCancelledEmailDTO,
    QrCheckinEmailDTO,
)
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

_GREEN = colors.HexColor("#27ae60")
_DARK = colors.HexColor("#2c3e50")
_LIGHT_GRAY = colors.HexColor("#f2f2f2")
_MID_GRAY = colors.HexColor("#95a5a6")
_RED = colors.HexColor("#c0392b")


# ── PDF builder ───────────────────────────────────────────────────────────────


def _build_qr_pdf(dto: QrCheckinEmailDTO) -> bytes:
    """Generate a PDF with QR image + booking details."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    brand = ParagraphStyle(
        "brand", fontSize=22, textColor=_GREEN, fontName="Helvetica-Bold", spaceAfter=2
    )
    tagline = ParagraphStyle(
        "tagline", fontSize=9, textColor=_MID_GRAY, fontName="Helvetica", spaceAfter=12
    )
    title = ParagraphStyle(
        "title", fontSize=16, textColor=_DARK, fontName="Helvetica-Bold", spaceAfter=6
    )
    section_header = ParagraphStyle(
        "section",
        fontSize=11,
        textColor=_DARK,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=6,
    )
    instructions_style = ParagraphStyle(
        "instructions", fontSize=9, textColor=_DARK, fontName="Helvetica", spaceAfter=4
    )
    footer_style = ParagraphStyle(
        "footer", fontSize=8, textColor=_MID_GRAY, fontName="Helvetica", alignment=1
    )

    col_w = [5 * cm, 11.7 * cm]

    def _row_table(data: list[list]) -> Table:
        t = Table(data, colWidths=col_w)
        style_cmds = [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), _DARK),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]
        for i in range(len(data)):
            bg = _LIGHT_GRAY if i % 2 else colors.white
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
        t.setStyle(TableStyle(style_cmds))
        return t

    # Decode QR bytes
    qr_bytes = base64.b64decode(dto.qr_code)
    qr_img_buffer = io.BytesIO(qr_bytes)
    qr_image = Image(qr_img_buffer, width=6 * cm, height=6 * cm)

    story = []

    story.append(Paragraph("TravelHub", brand))
    story.append(Paragraph("Tu plataforma de viajes de confianza", tagline))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_GREEN, spaceAfter=10))
    story.append(Paragraph("QR DE CHECK-IN", title))
    story.append(
        Paragraph(
            f"Reserva: <b>{dto.reservation_code}</b>", instructions_style
        )
    )
    story.append(Spacer(1, 8))

    # QR centered
    qr_table = Table([[qr_image]], colWidths=[16.7 * cm])
    qr_table.setStyle(
        TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")])
    )
    story.append(qr_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Detalles de la Reserva", section_header))
    story.append(
        _row_table(
            [
                ["Código de reserva", dto.reservation_code],
                ["Huésped", dto.guest_name],
                ["Hospedaje", dto.property_name],
                ["Dirección", dto.property_address],
                ["Tipo de habitación", dto.room_type],
                ["Check-in", dto.check_in.strftime("%d/%m/%Y")],
                ["Check-out", dto.check_out.strftime("%d/%m/%Y")],
                ["Número de huéspedes", str(dto.num_guests)],
            ]
        )
    )

    story.append(Paragraph("Instrucciones de uso", section_header))
    for step in [
        "1. Presente este código QR al llegar a recepción.",
        "2. El personal escaneará el código con su dispositivo.",
        "3. El check-in se registrará automáticamente.",
        "4. Guarde este documento como respaldo — funciona sin internet.",
    ]:
        story.append(Paragraph(step, instructions_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_MID_GRAY, spaceAfter=8))
    story.append(
        Paragraph(
            "Documento generado automáticamente por TravelHub · notificaciones_ms",
            footer_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()


# ── HTML builder ──────────────────────────────────────────────────────────────


def _build_qr_html(dto: QrCheckinEmailDTO) -> str:
    def row(label: str, value: str, alt: bool = False) -> str:
        bg = "#f2f2f2" if alt else "#ffffff"
        return (
            f'<tr style="background:{bg};">'
            f"<td style='padding:8px;border:1px solid #ddd;font-weight:bold;width:40%;'>{label}</td>"
            f"<td style='padding:8px;border:1px solid #ddd;'>{value}</td></tr>"
        )

    return f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
<h2 style="color:#27ae60;">TravelHub</h2>
<p style="color:#95a5a6;font-size:11px;margin-top:-10px;">Tu plataforma de viajes de confianza</p>
<hr style="border-color:#27ae60;">

<h3 style="color:#2c3e50;">Tu código QR de Check-In</h3>
<p>Estimado/a <b>{dto.guest_name}</b>,</p>
<p>Tu reserva <b>{dto.reservation_code}</b> ha sido confirmada. Aquí está tu código QR
para registrar el check-in en <b>{dto.property_name}</b>.</p>

<div style="text-align:center;margin:24px 0;">
  <img src="data:image/png;base64,{dto.qr_code}"
       alt="QR Check-In {dto.reservation_code}"
       style="width:200px;height:200px;border:1px solid #ddd;padding:8px;">
  <p style="font-size:12px;color:#7f8c8d;">
    El QR también está adjunto como imagen PNG y como PDF imprimible.
  </p>
</div>

<h4 style="color:#2c3e50;">Detalles de tu reserva</h4>
<table border="0" cellpadding="0" cellspacing="0"
       style="border-collapse:collapse;width:100%;margin-bottom:16px;">
  {row("Código de reserva", dto.reservation_code)}
  {row("Hospedaje", dto.property_name, True)}
  {row("Dirección", dto.property_address)}
  {row("Tipo de habitación", dto.room_type, True)}
  {row("Check-in", dto.check_in.strftime("%d/%m/%Y"))}
  {row("Check-out", dto.check_out.strftime("%d/%m/%Y"), True)}
  {row("Número de huéspedes", str(dto.num_guests))}
</table>

<h4 style="color:#2c3e50;">¿Cómo usar tu QR al llegar al hotel?</h4>
<ol style="color:#2c3e50;line-height:1.8;">
  <li>Muestra este correo o la aplicación TravelHub en tu teléfono al llegar a recepción.</li>
  <li>El personal escaneará el código QR con su dispositivo.</li>
  <li>Tu check-in se registrará de forma inmediata y automática.</li>
  <li>También puedes imprimir el PDF adjunto como respaldo sin necesidad de internet.</li>
</ol>

<p style="background:#eafaf1;border-left:4px solid #27ae60;padding:12px;border-radius:4px;">
  <b>Consejo:</b> Guarda este correo o descarga el PDF adjunto. El código QR funciona
  incluso sin conexión a internet desde la aplicación TravelHub.
</p>

<p>Gracias por elegir TravelHub. ¡Que disfrutes tu estancia!</p>
<p style="color:#95a5a6;font-size:11px;">
  notificaciones_ms — email automático · reserva {dto.reservation_code}
</p>
</body></html>
"""


def _build_cancelled_html(dto: QrCancelledEmailDTO) -> str:
    return f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
<h2 style="color:#27ae60;">TravelHub</h2>
<hr style="border-color:#c0392b;">

<h3 style="color:#c0392b;">Código QR invalidado</h3>
<p>Estimado/a <b>{dto.guest_name}</b>,</p>
<p>Te informamos que el código QR de check-in asociado a tu reserva
<b>{dto.reservation_code}</b> ha sido <b>invalidado</b> debido a la cancelación de la reserva.</p>

<table border="0" cellpadding="0" cellspacing="0"
       style="border-collapse:collapse;width:100%;margin:16px 0;">
  <tr style="background:#f2f2f2;">
    <td style="padding:8px;border:1px solid #ddd;font-weight:bold;">Código de reserva</td>
    <td style="padding:8px;border:1px solid #ddd;">{dto.reservation_code}</td>
  </tr>
  <tr>
    <td style="padding:8px;border:1px solid #ddd;font-weight:bold;">Hospedaje</td>
    <td style="padding:8px;border:1px solid #ddd;">{dto.property_name}</td>
  </tr>
  <tr style="background:#f2f2f2;">
    <td style="padding:8px;border:1px solid #ddd;font-weight:bold;">Check-in</td>
    <td style="padding:8px;border:1px solid #ddd;">{dto.check_in.strftime("%d/%m/%Y")}</td>
  </tr>
  <tr>
    <td style="padding:8px;border:1px solid #ddd;font-weight:bold;">Check-out</td>
    <td style="padding:8px;border:1px solid #ddd;">{dto.check_out.strftime("%d/%m/%Y")}</td>
  </tr>
</table>

<p style="background:#fdf2f2;border-left:4px solid #c0392b;padding:12px;border-radius:4px;">
  <b>Importante:</b> Este código QR ya <b>no es válido</b> para realizar check-in.
  Si intentas usarlo, el hotel lo rechazará automáticamente.
</p>

<p>Si crees que esto es un error o necesitas ayuda, contáctanos desde la aplicación TravelHub.</p>
<p style="color:#95a5a6;font-size:11px;">
  notificaciones_ms — email automático · reserva {dto.reservation_code}
</p>
</body></html>
"""


# ── Send functions ────────────────────────────────────────────────────────────


async def send_qr_checkin_email(dto: QrCheckinEmailDTO) -> bool:
    """Send QR check-in email with inline image, PNG attachment and PDF. Returns True on success."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("smtp_not_configured — skipping QR check-in email")
        return False

    subject = f"Tu QR de Check-In - Reserva {dto.reservation_code}"

    try:
        pdf_bytes = _build_qr_pdf(dto)
    except Exception as exc:
        logger.error("qr_pdf_build_error reservation_code=%s error=%s", dto.reservation_code, exc)
        return False

    qr_bytes = base64.b64decode(dto.qr_code)

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = dto.guest_email

    msg.attach(MIMEText(_build_qr_html(dto), "html"))

    # PNG attachment (C3)
    png_attachment = MIMEImage(qr_bytes, _subtype="png")
    png_attachment.add_header(
        "Content-Disposition", "attachment", filename=f"qr-checkin-{dto.reservation_code}.png"
    )
    msg.attach(png_attachment)

    # PDF attachment (C3)
    pdf_attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_attachment.add_header(
        "Content-Disposition", "attachment", filename=f"checkin-{dto.reservation_code}.pdf"
    )
    msg.attach(pdf_attachment)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, dto.guest_email, msg.as_string())
        logger.info(
            "qr_checkin_email_sent reservation_code=%s guest_email=%s",
            dto.reservation_code,
            dto.guest_email,
        )
        return True
    except Exception as exc:
        logger.error(
            "qr_checkin_email_error reservation_code=%s error=%s",
            dto.reservation_code,
            exc,
        )
        return False


async def send_qr_cancelled_email(dto: QrCancelledEmailDTO) -> bool:
    """Send QR invalidation email on booking cancellation. Returns True on success."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("smtp_not_configured — skipping QR cancelled email")
        return False

    subject = f"Tu código QR ha sido invalidado - Reserva {dto.reservation_code}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = dto.guest_email
    msg.attach(MIMEText(_build_cancelled_html(dto), "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, dto.guest_email, msg.as_string())
        logger.info(
            "qr_cancelled_email_sent reservation_code=%s guest_email=%s",
            dto.reservation_code,
            dto.guest_email,
        )
        return True
    except Exception as exc:
        logger.error(
            "qr_cancelled_email_error reservation_code=%s error=%s",
            dto.reservation_code,
            exc,
        )
        return False
