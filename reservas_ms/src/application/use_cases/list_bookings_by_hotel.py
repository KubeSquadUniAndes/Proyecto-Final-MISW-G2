from uuid import UUID

from src.application.dtos.booking_dto import BookingResponseDTO
from src.application.use_cases.create_booking import _build_response
from src.domain.repositories.booking_repository_port import BookingRepositoryPort


class ListBookingsByHotelUseCase:
    def __init__(self, booking_repo: BookingRepositoryPort) -> None:
        self._repo = booking_repo

    async def execute(self, hotel_id: UUID) -> list[BookingResponseDTO]:
        bookings = await self._repo.list_by_hotel(hotel_id)
        return [_build_response(b) for b in bookings]
