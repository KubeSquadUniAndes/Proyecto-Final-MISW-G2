from uuid import UUID, uuid4

from src.application.dtos.hotel_image_dto import HotelImageResponseDTO
from src.domain.entities.hotel_image import HotelImage
from src.domain.repositories.hotel_image_repository_port import HotelImageRepositoryPort
from src.domain.services.image_storage_port import ImageStoragePort

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class UploadHotelImageUseCase:
    def __init__(
        self,
        repo: HotelImageRepositoryPort,
        storage: ImageStoragePort,
    ) -> None:
        self._repo = repo
        self._storage = storage

    async def execute(
        self,
        hotel_id: UUID,
        data: bytes,
        content_type: str,
        filename: str,
    ) -> HotelImageResponseDTO:
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"Unsupported content type: {content_type}. Allowed: jpeg, png, webp, gif"
            )
        if len(data) > MAX_SIZE_BYTES:
            raise ValueError("File exceeds maximum size of 5 MB")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        key = f"hotels/{hotel_id}/{uuid4()}.{ext}"

        url = await self._storage.upload(key, data, content_type)

        saved = await self._repo.save(
            HotelImage(hotel_id=hotel_id, url=url, s3_key=key)
        )

        return HotelImageResponseDTO(
            id=saved.id,
            hotel_id=saved.hotel_id,
            url=saved.url,
            created_at=saved.created_at,
        )
