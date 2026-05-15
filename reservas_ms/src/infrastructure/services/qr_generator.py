"""QR code generation service for booking check-in."""

import base64
import io
import json
import logging
from uuid import UUID

import qrcode
import qrcode.constants

logger = logging.getLogger(__name__)


def generate_booking_qr(
    booking_code: str,
    booking_id: UUID,
    guest_name: str | None,
    check_in: str,
    check_out: str,
    room_type: str | None,
) -> str:
    """Generate a QR code for booking check-in.

    The QR payload contains the data needed for the hotel to validate
    the booking on arrival. Returns a base64-encoded PNG string so the
    mobile app can render it directly and cache it for offline use.

    Args:
        booking_code: Human-readable code (e.g. "TH-2026-XXXXX").
        booking_id: Unique booking UUID (prevents duplication/reuse).
        guest_name: Primary guest name.
        check_in: Check-in date as "YYYY-MM-DD".
        check_out: Check-out date as "YYYY-MM-DD".
        room_type: Room category (e.g. "Doble estándar").

    Returns:
        Base64-encoded PNG string of the QR code image.
    """
    payload = json.dumps(
        {
            "booking_code": booking_code,
            "booking_id": str(booking_id),
            "guest_name": guest_name or "",
            "check_in": check_in,
            "check_out": check_out,
            "room_type": room_type or "",
        },
        ensure_ascii=False,
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")
