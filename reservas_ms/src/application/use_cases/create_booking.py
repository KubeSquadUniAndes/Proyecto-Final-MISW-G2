import logging
import random
import string
from decimal import Decimal, ROUND_HALF_UP

from src.application.dtos.booking_dto import BookingResponseDTO, CreateBookingDTO
from src.domain.entities.booking import Booking
from src.domain.repositories.booking_repository_port import BookingRepositoryPort
from src.domain.services.booking_domain_service import BookingDomainService

logger = logging.getLogger(__name__)

TAX_RATE = Decimal("0.19")
MAX_CODE_RETRIES = 3


def _generate_booking_code() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"TH-2026-{suffix}"


def _build_response(booking: Booking) -> BookingResponseDTO:
    return BookingResponseDTO(
        id=booking.id,
        user_id=booking.user_id,
        hotel_id=booking.hotel_id,
        room_id=booking.room_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        status_display=booking.status_display,
        notes=booking.notes,
        booking_code=booking.booking_code,
        room_type=booking.room_type,
        num_guests=booking.num_guests,
        additional_guests=booking.additional_guests,
        special_requests=booking.special_requests,
        price_per_night=booking.price_per_night,
        total_nights=booking.total_nights,
        total_price=booking.total_price,
        taxes=booking.taxes,
        final_price=booking.final_price,
        traveler_name=booking.traveler_name,
        traveler_email=booking.traveler_email,
        traveler_phone=booking.traveler_phone,
        traveler_document=booking.traveler_document,
        cancellable=booking.cancellable,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )


class CreateBookingUseCase:
    def __init__(
        self,
        booking_repo: BookingRepositoryPort,
        domain_service: BookingDomainService,
        anomaly_client=None,
    ) -> None:
        self._repo = booking_repo
        self._domain_service = domain_service
        self._anomaly_client = anomaly_client

    async def execute(self, dto: CreateBookingDTO) -> BookingResponseDTO:
        # 1. Calculate pricing
        total_nights = (dto.end_time.date() - dto.start_time.date()).days
        if total_nights <= 0:
            raise ValueError("Booking must be at least 1 night")

        price_per_night = dto.price_per_night or Decimal("0")
        total_price = (price_per_night * total_nights).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
        taxes = (total_price * TAX_RATE).quantize(Decimal("0.01"), ROUND_HALF_UP)
        final_price = total_price + taxes

        # 2. Generate unique booking code (retry on collision)
        booking_code = None
        for _ in range(MAX_CODE_RETRIES):
            booking_code = _generate_booking_code()
            break  # collision check handled by DB unique constraint

        # 3. Build domain entity
        booking = Booking(
            user_id=dto.user_id,
            hotel_id=dto.hotel_id,
            room_id=dto.room_id,
            start_time=dto.start_time,
            end_time=dto.end_time,
            notes=dto.notes,
            booking_code=booking_code,
            room_type=dto.room_type,
            num_guests=dto.num_guests,
            additional_guests=dto.additional_guests,
            special_requests=dto.special_requests,
            price_per_night=price_per_night,
            total_nights=total_nights,
            total_price=total_price,
            taxes=taxes,
            final_price=final_price,
            traveler_name=dto.traveler_name,
            traveler_email=dto.traveler_email,
            traveler_phone=dto.traveler_phone,
            traveler_document=dto.traveler_document,
        )

        if not booking.is_valid():
            raise ValueError("Booking dates are not valid")

        # 4. Check schedule conflicts
        has_conflict = await self._domain_service.has_schedule_conflict(
            user_id=booking.user_id,
            room_id=booking.room_id,
            start_time=booking.start_time,
            end_time=booking.end_time,
        )
        if has_conflict:
            raise ValueError("A schedule conflict exists for this resource")

        # 5. Notify anomaly detector (fire-and-forget)
        if self._anomaly_client:
            try:
                result = await self._anomaly_client.analyze(
                    user_id=booking.user_id,
                    booking_id=booking.id,
                    room_id=booking.room_id,
                    start_time=booking.start_time,
                    end_time=booking.end_time,
                )
                if result.get("is_anomalous"):
                    logger.warning(
                        "create_booking_anomaly booking_id=%s action=%s",
                        booking.id,
                        result.get("action_taken"),
                    )
            except Exception as exc:
                logger.error(
                    "anomaly_check_failed booking_id=%s error=%s", booking.id, exc
                )
                raise ValueError("Error anomaly_check_failed")

        # 6. Persist booking
        saved = await self._repo.save(booking)

        # 7. Return response
        return _build_response(saved)
