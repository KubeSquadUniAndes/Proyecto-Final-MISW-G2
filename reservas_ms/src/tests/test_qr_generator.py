"""Unit tests for the QR code generator service."""

import base64
import json
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest
import qrcode

from src.infrastructure.services.qr_generator import generate_booking_qr

BOOKING_CODE = "TH-2026-AB3XY"
BOOKING_ID = uuid4()
GUEST_NAME = "Juan Pérez"
CHECK_IN = "2026-06-10"
CHECK_OUT = "2026-06-13"
ROOM_TYPE = "Doble estándar"


def _generate_default(**overrides) -> str:
    kwargs = dict(
        booking_code=BOOKING_CODE,
        booking_id=BOOKING_ID,
        guest_name=GUEST_NAME,
        check_in=CHECK_IN,
        check_out=CHECK_OUT,
        room_type=ROOM_TYPE,
    )
    kwargs.update(overrides)
    return generate_booking_qr(**kwargs)


def _capture_payload(**overrides) -> dict:
    """Run generate_booking_qr and capture the JSON handed to add_data."""
    captured = {}

    def fake_add_data(self, data):
        captured["payload"] = json.loads(data)

    with patch.object(qrcode.QRCode, "add_data", fake_add_data):
        # make() and make_image() need a real QRCode object, so we still
        # need to call them — just patch make_image to return a dummy
        mock_img = MagicMock()
        mock_img.save = lambda buf, format: buf.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
        with patch.object(qrcode.QRCode, "make_image", return_value=mock_img):
            with patch.object(qrcode.QRCode, "make"):
                _generate_default(**overrides)

    return captured.get("payload", {})


# ── Output format ─────────────────────────────────────────────────────────────


def test_returns_non_empty_string():
    result = _generate_default()
    assert isinstance(result, str)
    assert len(result) > 0


def test_output_is_valid_base64():
    result = _generate_default()
    try:
        decoded = base64.b64decode(result)
    except Exception as exc:
        pytest.fail(f"Output is not valid base64: {exc}")
    assert len(decoded) > 0


def test_output_is_png():
    """PNG files start with the magic bytes 0x89 PNG."""
    result = _generate_default()
    decoded = base64.b64decode(result)
    assert decoded[:4] == b"\x89PNG", "QR output is not a PNG file"


# ── Payload contents ──────────────────────────────────────────────────────────


def test_payload_contains_booking_code():
    payload = _capture_payload()
    assert payload["booking_code"] == BOOKING_CODE


def test_payload_contains_booking_id():
    payload = _capture_payload()
    assert payload["booking_id"] == str(BOOKING_ID)


def test_payload_contains_check_in():
    payload = _capture_payload()
    assert payload["check_in"] == CHECK_IN


def test_payload_contains_check_out():
    payload = _capture_payload()
    assert payload["check_out"] == CHECK_OUT


def test_payload_contains_guest_name():
    payload = _capture_payload()
    assert payload["guest_name"] == GUEST_NAME


def test_payload_contains_room_type():
    payload = _capture_payload()
    assert payload["room_type"] == ROOM_TYPE


# ── Edge cases ────────────────────────────────────────────────────────────────


def test_none_guest_name_defaults_to_empty_string():
    payload = _capture_payload(guest_name=None)
    assert payload["guest_name"] == ""


def test_none_room_type_defaults_to_empty_string():
    payload = _capture_payload(room_type=None)
    assert payload["room_type"] == ""


def test_payload_is_valid_json():
    """The data fed to the QR encoder must be deserializable JSON."""
    captured = {}

    def fake_add_data(self, data):
        captured["raw"] = data

    with patch.object(qrcode.QRCode, "add_data", fake_add_data):
        with patch.object(qrcode.QRCode, "make"):
            mock_img = MagicMock()
            mock_img.save = lambda buf, format: buf.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
            with patch.object(qrcode.QRCode, "make_image", return_value=mock_img):
                _generate_default()

    parsed = json.loads(captured["raw"])
    assert isinstance(parsed, dict)


# ── Uniqueness (criteria 3) ───────────────────────────────────────────────────


def test_different_booking_ids_produce_different_qrs():
    """Two bookings with different IDs must produce different QR images."""
    qr1 = generate_booking_qr(
        booking_code=BOOKING_CODE,
        booking_id=uuid4(),
        guest_name=GUEST_NAME,
        check_in=CHECK_IN,
        check_out=CHECK_OUT,
        room_type=ROOM_TYPE,
    )
    qr2 = generate_booking_qr(
        booking_code=BOOKING_CODE,
        booking_id=uuid4(),
        guest_name=GUEST_NAME,
        check_in=CHECK_IN,
        check_out=CHECK_OUT,
        room_type=ROOM_TYPE,
    )
    assert qr1 != qr2


def test_same_booking_produces_identical_qr():
    """Same inputs → same output (deterministic)."""
    fixed_id = uuid4()
    qr1 = generate_booking_qr(
        booking_code=BOOKING_CODE,
        booking_id=fixed_id,
        guest_name=GUEST_NAME,
        check_in=CHECK_IN,
        check_out=CHECK_OUT,
        room_type=ROOM_TYPE,
    )
    qr2 = generate_booking_qr(
        booking_code=BOOKING_CODE,
        booking_id=fixed_id,
        guest_name=GUEST_NAME,
        check_in=CHECK_IN,
        check_out=CHECK_OUT,
        room_type=ROOM_TYPE,
    )
    assert qr1 == qr2
