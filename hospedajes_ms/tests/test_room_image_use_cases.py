"""Unit tests for room image use cases."""

from decimal import Decimal
from uuid import uuid4

import pytest

from src.application.use_cases.delete_room_image import DeleteRoomImageUseCase
from src.application.use_cases.list_room_images import ListRoomImagesUseCase
from src.application.use_cases.upload_room_image import UploadRoomImageUseCase
from src.domain.entities.room import Room, RoomStatus, RoomType
from src.domain.entities.room_image import RoomImage


class MockRoomRepository:
    def __init__(self):
        self.rooms = {}

    async def save(self, room):
        self.rooms[room.id] = room
        return room

    async def get_by_id(self, room_id):
        return self.rooms.get(room_id)

    async def list_all(self, hotel_id=None):
        return list(self.rooms.values())

    async def update(self, room):
        self.rooms[room.id] = room
        return room

    async def delete(self, room_id):
        if room_id in self.rooms:
            del self.rooms[room_id]
            return True
        return False

    async def count_by_status(self, status):
        return len([r for r in self.rooms.values() if r.status == status])

    async def count_total(self):
        return len(self.rooms)


class MockRoomImageRepository:
    def __init__(self):
        self.images = {}

    async def save(self, image):
        self.images[image.id] = image
        return image

    async def get_by_id(self, image_id):
        return self.images.get(image_id)

    async def list_by_room(self, room_id):
        return [img for img in self.images.values() if img.room_id == room_id]

    async def delete(self, image_id):
        if image_id in self.images:
            del self.images[image_id]
            return True
        return False


class MockImageStorage:
    def __init__(self):
        self.uploaded = {}
        self.deleted = []

    async def upload(self, key, data, content_type):
        self.uploaded[key] = data
        return f"https://s3.example.com/{key}"

    async def delete(self, key):
        self.deleted.append(key)


def make_room(hotel_id=None):
    return Room(
        hotel_id=hotel_id or uuid4(),
        name="Room 101",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("100.00"),
        capacity=2,
        beds="1 Double",
        size=25.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )


@pytest.mark.asyncio
async def test_upload_room_image_success():
    hotel_id = uuid4()
    room = make_room(hotel_id=hotel_id)
    room_repo = MockRoomRepository()
    room_repo.rooms[room.id] = room
    image_repo = MockRoomImageRepository()
    storage = MockImageStorage()

    use_case = UploadRoomImageUseCase(room_repo, image_repo, storage)
    result = await use_case.execute(
        room_id=room.id,
        hotel_id=hotel_id,
        data=b"fake image data",
        content_type="image/jpeg",
        filename="photo.jpg",
    )

    assert result.room_id == room.id
    assert "photo.jpg" in result.url or result.url.startswith("https://")
    assert len(image_repo.images) == 1


@pytest.mark.asyncio
async def test_upload_room_image_room_not_found():
    room_repo = MockRoomRepository()
    image_repo = MockRoomImageRepository()
    storage = MockImageStorage()

    use_case = UploadRoomImageUseCase(room_repo, image_repo, storage)
    with pytest.raises(ValueError, match="not found"):
        await use_case.execute(
            room_id=uuid4(),
            hotel_id=uuid4(),
            data=b"data",
            content_type="image/jpeg",
            filename="photo.jpg",
        )


@pytest.mark.asyncio
async def test_upload_room_image_wrong_hotel():
    room = make_room(hotel_id=uuid4())
    room_repo = MockRoomRepository()
    room_repo.rooms[room.id] = room
    image_repo = MockRoomImageRepository()
    storage = MockImageStorage()

    use_case = UploadRoomImageUseCase(room_repo, image_repo, storage)
    with pytest.raises(PermissionError, match="does not belong"):
        await use_case.execute(
            room_id=room.id,
            hotel_id=uuid4(),  # different hotel
            data=b"data",
            content_type="image/jpeg",
            filename="photo.jpg",
        )


@pytest.mark.asyncio
async def test_upload_room_image_invalid_content_type():
    hotel_id = uuid4()
    room = make_room(hotel_id=hotel_id)
    room_repo = MockRoomRepository()
    room_repo.rooms[room.id] = room
    image_repo = MockRoomImageRepository()
    storage = MockImageStorage()

    use_case = UploadRoomImageUseCase(room_repo, image_repo, storage)
    with pytest.raises(ValueError, match="Unsupported content type"):
        await use_case.execute(
            room_id=room.id,
            hotel_id=hotel_id,
            data=b"data",
            content_type="application/pdf",
            filename="file.pdf",
        )


@pytest.mark.asyncio
async def test_upload_room_image_exceeds_size():
    hotel_id = uuid4()
    room = make_room(hotel_id=hotel_id)
    room_repo = MockRoomRepository()
    room_repo.rooms[room.id] = room
    image_repo = MockRoomImageRepository()
    storage = MockImageStorage()

    use_case = UploadRoomImageUseCase(room_repo, image_repo, storage)
    with pytest.raises(ValueError, match="5 MB"):
        await use_case.execute(
            room_id=room.id,
            hotel_id=hotel_id,
            data=b"x" * (5 * 1024 * 1024 + 1),
            content_type="image/jpeg",
            filename="big.jpg",
        )


@pytest.mark.asyncio
async def test_list_room_images():
    room_id = uuid4()
    image_repo = MockRoomImageRepository()
    img1 = RoomImage(room_id=room_id, url="https://s3/1.jpg", s3_key="rooms/1.jpg")
    img2 = RoomImage(room_id=room_id, url="https://s3/2.jpg", s3_key="rooms/2.jpg")
    image_repo.images[img1.id] = img1
    image_repo.images[img2.id] = img2

    use_case = ListRoomImagesUseCase(image_repo)
    result = await use_case.execute(room_id)

    assert len(result) == 2
    assert all(r.room_id == room_id for r in result)


@pytest.mark.asyncio
async def test_list_room_images_empty():
    image_repo = MockRoomImageRepository()
    use_case = ListRoomImagesUseCase(image_repo)
    result = await use_case.execute(uuid4())
    assert result == []


@pytest.mark.asyncio
async def test_delete_room_image_success():
    hotel_id = uuid4()
    room = make_room(hotel_id=hotel_id)
    room_repo = MockRoomRepository()
    room_repo.rooms[room.id] = room

    image = RoomImage(room_id=room.id, url="https://s3/1.jpg", s3_key="rooms/1.jpg")
    image_repo = MockRoomImageRepository()
    image_repo.images[image.id] = image
    storage = MockImageStorage()

    use_case = DeleteRoomImageUseCase(room_repo, image_repo, storage)
    await use_case.execute(image_id=image.id, hotel_id=hotel_id)

    assert image.id not in image_repo.images
    assert "rooms/1.jpg" in storage.deleted


@pytest.mark.asyncio
async def test_delete_room_image_not_found():
    room_repo = MockRoomRepository()
    image_repo = MockRoomImageRepository()
    storage = MockImageStorage()

    use_case = DeleteRoomImageUseCase(room_repo, image_repo, storage)
    with pytest.raises(ValueError, match="not found"):
        await use_case.execute(image_id=uuid4(), hotel_id=uuid4())


@pytest.mark.asyncio
async def test_delete_room_image_wrong_hotel():
    hotel_id = uuid4()
    room = make_room(hotel_id=hotel_id)
    room_repo = MockRoomRepository()
    room_repo.rooms[room.id] = room

    image = RoomImage(room_id=room.id, url="https://s3/1.jpg", s3_key="rooms/1.jpg")
    image_repo = MockRoomImageRepository()
    image_repo.images[image.id] = image
    storage = MockImageStorage()

    use_case = DeleteRoomImageUseCase(room_repo, image_repo, storage)
    with pytest.raises(PermissionError, match="does not belong"):
        await use_case.execute(image_id=image.id, hotel_id=uuid4())
