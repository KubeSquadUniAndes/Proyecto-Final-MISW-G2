from uuid import UUID

from src.application.dtos.booking_dto import BookingResponseDTO
from src.application.use_cases.create_booking import _build_response
from src.domain.repositories.booking_repository_port import BookingRepositoryPort


class ListBookingsUseCase:
    def __init__(self, booking_repo: BookingRepositoryPort) -> None:
        self._repo = booking_repo

    async def execute(self, user_id: UUID) -> list[BookingResponseDTO]:
        bookings = await self._repo.get_active_by_user(user_id)
        return [_build_response(b) for b in bookings]
