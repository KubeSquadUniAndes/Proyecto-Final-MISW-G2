from uuid import UUID

from src.application.dtos.hotel_image_dto import HotelImageResponseDTO
from src.domain.repositories.hotel_image_repository_port import HotelImageRepositoryPort


class ListHotelImagesUseCase:
    def __init__(self, repo: HotelImageRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, hotel_id: UUID) -> list[HotelImageResponseDTO]:
        images = await self._repo.list_by_hotel(hotel_id)
        return [
            HotelImageResponseDTO(
                id=img.id,
                hotel_id=img.hotel_id,
                url=img.url,
                created_at=img.created_at,
            )
            for img in images
        ]
