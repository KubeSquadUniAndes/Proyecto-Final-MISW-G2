import io
import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.application.dtos.payment_voucher_dto import PaymentVoucherDTO
from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

_GREEN = colors.HexColor("#27ae60")
_DARK = colors.HexColor("#2c3e50")
_LIGHT_GRAY = colors.HexColor("#f2f2f2")
_MID_GRAY = colors.HexColor("#95a5a6")


def _build_pdf(dto: PaymentVoucherDTO) -> bytes:
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
        "brand",
        fontSize=22,
        textColor=_GREEN,
        fontName="Helvetica-Bold",
        spaceAfter=2,
    )
    tagline = ParagraphStyle(
        "tagline",
        fontSize=9,
        textColor=_MID_GRAY,
        fontName="Helvetica",
        spaceAfter=12,
    )
    title = ParagraphStyle(
        "title",
        fontSize=16,
        textColor=_DARK,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    status_style = ParagraphStyle(
        "status",
        fontSize=11,
        textColor=_GREEN,
        fontName="Helvetica-Bold",
        spaceAfter=14,
    )
    section_header = ParagraphStyle(
        "section",
        fontSize=11,
        textColor=_DARK,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=6,
    )
    footer_style = ParagraphStyle(
        "footer",
        fontSize=8,
        textColor=_MID_GRAY,
        fontName="Helvetica",
        alignment=1,
    )

    paid_str = dto.paid_at.strftime("%d/%m/%Y %H:%M:%S")
    checkin_str = dto.check_in.strftime("%d/%m/%Y")
    checkout_str = dto.check_out.strftime("%d/%m/%Y")

    def _table(data: list[list], col_widths: list[float]) -> Table:
        t = Table(data, colWidths=col_widths)
        row_count = len(data)
        style_cmds = [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), _DARK),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUND", (0, 0), (-1, -1), [colors.white, _LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]
        for i in range(row_count):
            bg = _LIGHT_GRAY if i % 2 else colors.white
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
        t.setStyle(TableStyle(style_cmds))
        return t

    col_w = [5 * cm, 11.7 * cm]

    story = []

    # Header
    story.append(Paragraph("TravelHub", brand))
    story.append(Paragraph("Tu plataforma de viajes de confianza", tagline))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_GREEN, spaceAfter=10))

    story.append(Paragraph("VOUCHER DE PAGO", title))
    story.append(Paragraph("✔ Pago Confirmado", status_style))

    # Transaction details
    story.append(Paragraph("Detalles de la Transacción", section_header))
    story.append(
        _table(
            [
                ["Número de transacción", dto.transaction_id],
                ["Fecha y hora del pago", paid_str],
                ["Método de pago", dto.payment_method],
                ["Código de reserva", dto.reservation_code],
            ],
            col_w,
        )
    )

    # Traveler & property
    story.append(Paragraph("Datos del Viajero y Hospedaje", section_header))
    story.append(
        _table(
            [
                ["Viajero", dto.guest_name],
                ["Hospedaje", dto.property_name],
                ["Dirección", dto.property_address],
                ["Tipo de habitación", dto.room_type],
                ["Check-in", checkin_str],
                ["Check-out", checkout_str],
                ["Número de huéspedes", str(dto.num_guests)],
            ],
            col_w,
        )
    )

    # Price breakdown
    story.append(Paragraph("Desglose de Precios", section_header))
    price_data = [
        ["Tarifa por noche", f"${dto.nightly_rate:,.2f}"],
        ["Número de noches", str(dto.num_nights)],
        ["Subtotal", f"${dto.subtotal:,.2f}"],
        ["Impuestos", f"${dto.taxes:,.2f}"],
        ["Descuentos aplicados", f"-${dto.discounts:,.2f}"],
    ]
    price_table = Table(
        price_data + [["TOTAL PAGADO", f"${dto.total_amount:,.2f}"]], colWidths=col_w
    )
    price_style = [
        ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for i in range(len(price_data)):
        bg = _LIGHT_GRAY if i % 2 else colors.white
        price_style.append(("BACKGROUND", (0, i), (-1, i), bg))
    # Total row
    total_row = len(price_data)
    price_style += [
        ("BACKGROUND", (0, total_row), (-1, total_row), _GREEN),
        ("TEXTCOLOR", (0, total_row), (-1, total_row), colors.white),
        ("FONTNAME", (0, total_row), (-1, total_row), "Helvetica-Bold"),
        ("FONTSIZE", (0, total_row), (-1, total_row), 11),
    ]
    price_table.setStyle(TableStyle(price_style))
    story.append(price_table)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_MID_GRAY, spaceAfter=8))
    story.append(
        Paragraph(
            f"Documento generado automáticamente por TravelHub · notificaciones_ms · {paid_str}",
            footer_style,
        )
    )
    story.append(
        Paragraph(
            "Este voucher es el comprobante oficial de su transacción. Consérvelo para sus registros.",
            footer_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()


def _build_html(dto: PaymentVoucherDTO) -> str:
    paid_str = dto.paid_at.strftime("%d/%m/%Y %H:%M:%S")
    checkin_str = dto.check_in.strftime("%d/%m/%Y")
    checkout_str = dto.check_out.strftime("%d/%m/%Y")

    def row(label: str, value: str, alt: bool = False) -> str:
        bg = "#f2f2f2" if alt else "#ffffff"
        return (
            f'<tr style="background:{bg};">'
            f"<td style='padding:8px;border:1px solid #ddd;font-weight:bold;width:40%;'>{label}</td>"
            f"<td style='padding:8px;border:1px solid #ddd;'>{value}</td>"
            f"</tr>"
        )

    return f"""
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
<h2 style="color:#27ae60;">TravelHub</h2>
<p style="color:#95a5a6;font-size:11px;margin-top:-10px;">Tu plataforma de viajes de confianza</p>
<hr style="border-color:#27ae60;">

<h3 style="color:#2c3e50;">VOUCHER DE PAGO</h3>
<p><b style="color:#27ae60;">&#10004; Pago Confirmado</b></p>

<p>Estimado/a <b>{dto.guest_name}</b>,</p>
<p>Su pago ha sido procesado exitosamente. A continuación encontrará el detalle de su transacción.
El voucher en PDF está adjunto a este correo.</p>

<h4 style="color:#2c3e50;">Detalles de la Transacción</h4>
<table border="0" cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;margin-bottom:16px;">
{row("Número de transacción", dto.transaction_id, False)}
{row("Fecha y hora del pago", paid_str, True)}
{row("Método de pago", dto.payment_method, False)}
{row("Código de reserva", dto.reservation_code, True)}
</table>

<h4 style="color:#2c3e50;">Datos del Viajero y Hospedaje</h4>
<table border="0" cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;margin-bottom:16px;">
{row("Viajero", dto.guest_name, False)}
{row("Hospedaje", dto.property_name, True)}
{row("Dirección", dto.property_address, False)}
{row("Tipo de habitación", dto.room_type, True)}
{row("Check-in", checkin_str, False)}
{row("Check-out", checkout_str, True)}
{row("Número de huéspedes", str(dto.num_guests), False)}
</table>

<h4 style="color:#2c3e50;">Desglose de Precios</h4>
<table border="0" cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;margin-bottom:16px;">
{row("Tarifa por noche", f"${dto.nightly_rate:,.2f}", False)}
{row("Número de noches", str(dto.num_nights), True)}
{row("Subtotal", f"${dto.subtotal:,.2f}", False)}
{row("Impuestos", f"${dto.taxes:,.2f}", True)}
{row("Descuentos aplicados", f"-${dto.discounts:,.2f}", False)}
<tr style="background:#27ae60;">
  <td style="padding:10px;border:1px solid #27ae60;color:white;font-weight:bold;font-size:14px;">TOTAL PAGADO</td>
  <td style="padding:10px;border:1px solid #27ae60;color:white;font-weight:bold;font-size:14px;">${dto.total_amount:,.2f}</td>
</tr>
</table>

<p>Gracias por elegir TravelHub. Si tiene alguna consulta puede responder este correo o
contactarnos desde la aplicación.</p>

<p style="color:#95a5a6;font-size:11px;">
  notificaciones_ms — voucher de pago automático · {paid_str}
</p>
</body></html>
"""


async def send_payment_voucher_email(dto: PaymentVoucherDTO) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("smtp_not_configured — skipping payment voucher email")
        return False

    subject = f"Voucher de pago — Reserva {dto.reservation_code}"

    try:
        pdf_bytes = _build_pdf(dto)
    except Exception as exc:
        logger.error(
            "payment_voucher_pdf_error reservation_code=%s error=%s",
            dto.reservation_code,
            exc,
        )
        return False

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = dto.guest_email

    msg.attach(MIMEText(_build_html(dto), "html"))

    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=f"voucher-{dto.reservation_code}.pdf",
    )
    msg.attach(attachment)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, dto.guest_email, msg.as_string())
        logger.info(
            "payment_voucher_email_sent reservation_code=%s transaction_id=%s guest_email=%s",
            dto.reservation_code,
            dto.transaction_id,
            dto.guest_email,
        )
        return True
    except Exception as exc:
        logger.error(
            "payment_voucher_email_error reservation_code=%s error=%s",
            dto.reservation_code,
            exc,
        )
        return False
