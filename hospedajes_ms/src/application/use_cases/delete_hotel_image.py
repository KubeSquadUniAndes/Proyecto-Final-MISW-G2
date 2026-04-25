from uuid import UUID

from src.domain.repositories.hotel_image_repository_port import HotelImageRepositoryPort
from src.domain.services.image_storage_port import ImageStoragePort


class DeleteHotelImageUseCase:
    def __init__(
        self,
        repo: HotelImageRepositoryPort,
        storage: ImageStoragePort,
    ) -> None:
        self._repo = repo
        self._storage = storage

    async def execute(self, image_id: UUID, hotel_id: UUID) -> None:
        image = await self._repo.get_by_id(image_id)
        if not image:
            raise ValueError(f"Image {image_id} not found")
        if image.hotel_id != hotel_id:
            raise PermissionError("Image does not belong to this hotel")

        await self._storage.delete(image.s3_key)
        await self._repo.delete(image_id)
