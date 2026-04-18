import logging

from src.application.dtos.booking_dto import BookingResponseDTO, CancelBookingDTO
from src.domain.repositories.booking_repository_port import BookingRepositoryPort

logger = logging.getLogger(__name__)


class CancelBookingUseCase:
    def __init__(self, booking_repo: BookingRepositoryPort) -> None:
        self._repo = booking_repo

    async def execute(self, dto: CancelBookingDTO) -> BookingResponseDTO:
        # 1. Load booking
        booking = await self._repo.get_by_id(dto.booking_id)
        if not booking:
            raise LookupError(f"Booking {dto.booking_id} not found")

        # 2. Verify ownership
        if booking.user_id != dto.user_id:
            raise PermissionError("You do not have permission to cancel this booking")

        # 3. Verify cancellable state
        if not booking.cancellable:
            raise ValueError(f"Cannot cancel a booking with status '{booking.status}'")

        # 4. Cancel and persist
        booking.cancel()
        updated = await self._repo.update(booking)

        from src.application.use_cases.create_booking import _build_response

        return _build_response(updated)
