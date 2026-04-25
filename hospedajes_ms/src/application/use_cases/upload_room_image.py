from uuid import UUID, uuid4

from src.application.dtos.room_image_dto import RoomImageResponseDTO
from src.domain.entities.room_image import RoomImage
from src.domain.repositories.room_image_repository_port import RoomImageRepositoryPort
from src.domain.repositories.room_repository_port import RoomRepositoryPort
from src.domain.services.image_storage_port import ImageStoragePort

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class UploadRoomImageUseCase:
    def __init__(
        self,
        room_repo: RoomRepositoryPort,
        image_repo: RoomImageRepositoryPort,
        storage: ImageStoragePort,
    ) -> None:
        self._room_repo = room_repo
        self._image_repo = image_repo
        self._storage = storage

    async def execute(
        self,
        room_id: UUID,
        hotel_id: UUID,
        data: bytes,
        content_type: str,
        filename: str,
    ) -> RoomImageResponseDTO:
        room = await self._room_repo.get_by_id(room_id)
        if not room:
            raise ValueError(f"Room {room_id} not found")
        if room.hotel_id != hotel_id:
            raise PermissionError("Room does not belong to this hotel")

        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Unsupported content type: {content_type}. Allowed: jpeg, png, webp, gif")
        if len(data) > MAX_SIZE_BYTES:
            raise ValueError("File exceeds maximum size of 5 MB")

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        key = f"rooms/{room_id}/{uuid4()}.{ext}"

        url = await self._storage.upload(key, data, content_type)

        saved = await self._image_repo.save(RoomImage(room_id=room_id, url=url, s3_key=key))

        return RoomImageResponseDTO(
            id=saved.id,
            room_id=saved.room_id,
            url=saved.url,
            created_at=saved.created_at,
        )
