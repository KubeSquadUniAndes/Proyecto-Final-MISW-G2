from fastapi import APIRouter, Depends, HTTPException, Header, status

from src.application.dtos.payment_voucher_dto import PaymentVoucherDTO
from src.application.dtos.qr_checkin_email_dto import (
    QrCancelledEmailDTO,
    QrCheckinEmailDTO,
)
from src.application.dtos.reservation_confirmation_dto import ReservationConfirmationDTO
from src.application.use_cases.send_payment_voucher import SendPaymentVoucherUseCase
from src.application.use_cases.send_qr_checkin_email import (
    SendQrCancelledEmailUseCase,
    SendQrCheckinEmailUseCase,
)
from src.application.use_cases.send_reservation_confirmation import (
    SendReservationConfirmationUseCase,
)
from src.infrastructure.config.settings import settings
from src.infrastructure.http.schemas.payment_voucher_schema import (
    PaymentVoucherRequest,
    PaymentVoucherResponse,
)
from src.infrastructure.http.schemas.reservation_notification_schema import (
    QrCancelledEmailRequest,
    QrCheckinEmailRequest,
    QrEmailResponse,
    ReservationConfirmationRequest,
    ReservationConfirmationResponse,
)

router = APIRouter(prefix="/notifications", tags=["Reservations"])


async def require_internal_api_key(x_api_key: str = Header(...)) -> None:
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing internal API key",
        )


@router.post(
    "/reservations/confirmation",
    response_model=ReservationConfirmationResponse,
    status_code=status.HTTP_200_OK,
    summary="Send reservation confirmation email",
    description=(
        "Called by **reservas_ms** when a reservation reaches 'Confirmada' status. "
        "Sends a confirmation email to the guest with full reservation details.\n\n"
        "Requires `X-Api-Key` header. Email errors are logged but do not affect "
        "the reservation status."
    ),
    responses={403: {"description": "Invalid API key"}},
)
async def send_reservation_confirmation(
    body: ReservationConfirmationRequest,
    _: None = Depends(require_internal_api_key),
) -> ReservationConfirmationResponse:
    use_case = SendReservationConfirmationUseCase()
    dto = ReservationConfirmationDTO(**body.model_dump())
    result = await use_case.execute(dto)
    return ReservationConfirmationResponse(**result.model_dump())


@router.post(
    "/payment/voucher",
    response_model=PaymentVoucherResponse,
    status_code=status.HTTP_200_OK,
    summary="Send payment voucher email with PDF attachment",
    description=(
        "Called by **reservas_ms** (or the payment service) after a payment is confirmed. "
        "Sends an HTML email with a downloadable PDF voucher to the traveler.\n\n"
        "The same endpoint can be used to **resend** the voucher on demand.\n\n"
        "Requires `X-Api-Key` header. Email/PDF errors are logged but do not affect "
        "the payment or reservation status."
    ),
    responses={403: {"description": "Invalid API key"}},
)
async def send_payment_voucher(
    body: PaymentVoucherRequest,
    _: None = Depends(require_internal_api_key),
) -> PaymentVoucherResponse:
    use_case = SendPaymentVoucherUseCase()
    dto = PaymentVoucherDTO(**body.model_dump())
    result = await use_case.execute(dto)
    return PaymentVoucherResponse(**result.model_dump())


@router.post(
    "/reservations/qr-checkin",
    response_model=QrEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Send QR check-in email with PNG and PDF attachments",
    description=(
        "Called by **reservas_ms** after approving a booking and generating the QR. "
        "Also called on resend request (C5). "
        "Sends an email with the QR inline, a PNG attachment, and a PDF with booking details.\n\n"
        "Requires `X-Api-Key` header. Email errors are logged but do not affect the reservation."
    ),
    responses={403: {"description": "Invalid API key"}},
)
async def send_qr_checkin_email(
    body: QrCheckinEmailRequest,
    _: None = Depends(require_internal_api_key),
) -> QrEmailResponse:
    use_case = SendQrCheckinEmailUseCase()
    dto = QrCheckinEmailDTO(**body.model_dump())
    result = await use_case.execute(dto)
    return QrEmailResponse(**result.model_dump())


@router.post(
    "/reservations/qr-cancelled",
    response_model=QrEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Notify traveler that their QR has been invalidated (cancellation)",
    description=(
        "Called by **reservas_ms** when a confirmed booking with a QR is cancelled. "
        "Sends an email informing the traveler that the QR is no longer valid.\n\n"
        "Requires `X-Api-Key` header."
    ),
    responses={403: {"description": "Invalid API key"}},
)
async def send_qr_cancelled_email(
    body: QrCancelledEmailRequest,
    _: None = Depends(require_internal_api_key),
) -> QrEmailResponse:
    use_case = SendQrCancelledEmailUseCase()
    dto = QrCancelledEmailDTO(**body.model_dump())
    result = await use_case.execute(dto)
    return QrEmailResponse(**result.model_dump())
