from uuid import UUID

from src.domain.repositories.room_image_repository_port import RoomImageRepositoryPort
from src.domain.repositories.room_repository_port import RoomRepositoryPort
from src.domain.services.image_storage_port import ImageStoragePort


class DeleteRoomImageUseCase:
    def __init__(
        self,
        room_repo: RoomRepositoryPort,
        image_repo: RoomImageRepositoryPort,
        storage: ImageStoragePort,
    ) -> None:
        self._room_repo = room_repo
        self._image_repo = image_repo
        self._storage = storage

    async def execute(self, image_id: UUID, hotel_id: UUID) -> None:
        image = await self._image_repo.get_by_id(image_id)
        if not image:
            raise ValueError(f"Image {image_id} not found")

        room = await self._room_repo.get_by_id(image.room_id)
        if not room or room.hotel_id != hotel_id:
            raise PermissionError("Image does not belong to this hotel")

        await self._storage.delete(image.s3_key)
        await self._image_repo.delete(image_id)
