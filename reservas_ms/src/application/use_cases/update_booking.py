import logging
from datetime import datetime

from src.application.dtos.booking_dto import BookingResponseDTO, UpdateBookingDTO
from src.domain.repositories.booking_repository_port import BookingRepositoryPort
from src.domain.services.booking_domain_service import BookingDomainService

logger = logging.getLogger(__name__)


class UpdateBookingUseCase:
    """Input port: updates dates and/or notes of an existing booking.

    Flow:
    1. Load and verify ownership of the booking
    2. Apply changes and validate domain rules (date validity + conflict check)
    3. Persist the updated booking
    4. Notify detector_anomalias_ms (fire-and-forget)
    """

    def __init__(
        self,
        booking_repo: BookingRepositoryPort,
        domain_service: BookingDomainService,
        anomaly_client=None,
    ) -> None:
        self._repo = booking_repo
        self._domain_service = domain_service
        self._anomaly_client = anomaly_client

    async def execute(self, dto: UpdateBookingDTO) -> BookingResponseDTO:
        # 1. Load booking
        booking = await self._repo.get_by_id(dto.booking_id)
        if not booking:
            raise ValueError(f"Booking {dto.booking_id} not found")

        # 2. Verify ownership
        if booking.user_id != dto.user_id:
            raise PermissionError("You do not have permission to modify this booking")

        # 3. Apply only the provided fields
        if dto.notes is not None:
            booking.notes = dto.notes
        if dto.start_time is not None:
            booking.start_time = dto.start_time
        if dto.end_time is not None:
            booking.end_time = dto.end_time

        booking.updated_at = datetime.utcnow()

        # 4. Validate domain rules
        if not booking.is_valid():
            raise ValueError("Updated booking dates are not valid")

        has_conflict = await self._domain_service.has_schedule_conflict(
            user_id=booking.user_id,
            resource_id=booking.resource_id,
            start_time=booking.start_time,
            end_time=booking.end_time,
            exclude_booking_id=booking.id,
        )
        if has_conflict:
            raise ValueError("Updated dates conflict with an existing booking")

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
                        "update_booking_anomaly booking_id=%s action=%s",
                        booking.id,
                        result.get("action_taken"),
                    )
            except Exception as exc:
                logger.error(
                    "anomaly_check_failed booking_id=%s error=%s", booking.id, exc
                )
                raise ValueError("Error anomaly_check_failed")

        # 6. Persist
        updated = await self._repo.update(booking)

        return BookingResponseDTO(
            id=updated.id,
            user_id=updated.user_id,
            resource_id=updated.resource_id,
            start_time=updated.start_time,
            end_time=updated.end_time,
            status=updated.status,
            notes=updated.notes,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
