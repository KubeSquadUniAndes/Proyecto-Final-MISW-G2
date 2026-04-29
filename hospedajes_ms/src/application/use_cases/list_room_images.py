from uuid import UUID

from src.application.dtos.room_image_dto import RoomImageResponseDTO
from src.domain.repositories.room_image_repository_port import RoomImageRepositoryPort


class ListRoomImagesUseCase:
    def __init__(self, repo: RoomImageRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, room_id: UUID) -> list[RoomImageResponseDTO]:
        images = await self._repo.list_by_room(room_id)
        return [
            RoomImageResponseDTO(
                id=img.id,
                room_id=img.room_id,
                url=img.url,
                created_at=img.created_at,
            )
            for img in images
        ]
