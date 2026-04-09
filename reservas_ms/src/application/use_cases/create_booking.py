import logging

from src.application.dtos.booking_dto import BookingResponseDTO, CreateBookingDTO
from src.domain.entities.booking import Booking
from src.domain.repositories.booking_repository_port import BookingRepositoryPort
from src.domain.services.booking_domain_service import BookingDomainService

logger = logging.getLogger(__name__)


class CreateBookingUseCase:
    """Use case: orchestrates the logic to create a new booking."""

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
        # 1. Create domain entity
        booking = Booking(
            user_id=dto.user_id,
            resource_id=dto.resource_id,
            start_time=dto.start_time,
            end_time=dto.end_time,
            notes=dto.notes,
        )

        # 2. Validate domain rules
        if not booking.is_valid():
            raise ValueError("Booking dates are not valid")

        # 3. Check for schedule conflicts
        has_conflict = await self._domain_service.has_schedule_conflict(
            user_id=booking.user_id,
            resource_id=booking.resource_id,
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
                    resource_id=booking.resource_id,
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

        # 5. Persist the booking
        saved_booking = await self._repo.save(booking)

        return BookingResponseDTO(
            id=saved_booking.id,
            user_id=saved_booking.user_id,
            resource_id=saved_booking.resource_id,
            start_time=saved_booking.start_time,
            end_time=saved_booking.end_time,
            status=saved_booking.status,
            notes=saved_booking.notes,
            created_at=saved_booking.created_at,
            updated_at=saved_booking.updated_at,
        )
