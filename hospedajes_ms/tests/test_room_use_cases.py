"""Unit tests for hospedajes_ms use cases and entities."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.application.dtos.room_dto import CreateRoomDTO, UpdateRoomDTO
from src.application.use_cases.create_room import CreateRoomUseCase
from src.application.use_cases.delete_room import DeleteRoomUseCase
from src.application.use_cases.get_room import GetRoomUseCase
from src.application.use_cases.get_room_stats import GetRoomStatsUseCase
from src.application.use_cases.list_rooms import ListRoomsUseCase
from src.application.use_cases.update_room import UpdateRoomUseCase
from src.domain.entities.room import Room, RoomStatus, RoomType


class MockRoomRepository:
    def __init__(self):
        self.rooms = {}

    async def save(self, room):
        self.rooms[room.id] = room
        return room

    async def get_by_id(self, room_id):
        return self.rooms.get(room_id)

    async def list_all(self, hotel_id=None):
        rooms = list(self.rooms.values())
        if hotel_id is not None:
            rooms = [r for r in rooms if r.hotel_id == hotel_id]
        return rooms

    async def update(self, room):
        self.rooms[room.id] = room
        return room

    async def count_by_status(self, status):
        return len([r for r in self.rooms.values() if r.status == status])

    async def count_total(self):
        return len(self.rooms)

    async def delete(self, room_id):
        if room_id in self.rooms:
            del self.rooms[room_id]
            return True
        return False


@pytest.mark.asyncio
async def test_create_room_success():
    """Test successful room creation."""
    repo = MockRoomRepository()
    use_case = CreateRoomUseCase(repo)

    dto = CreateRoomDTO(
        hotel_id=uuid4(),
        name="Suite 101",
        room_type=RoomType.SUITE,
        price=Decimal("150.00"),
        capacity=2,
        beds="1 King",
        size=45.5,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi, TV, Minibar",
    )

    result = await use_case.execute(dto)

    assert result.name == "Suite 101"
    assert result.room_type == RoomType.SUITE
    assert result.price == Decimal("150.00")
    assert result.capacity == 2


@pytest.mark.asyncio
async def test_create_room_negative_price():
    """Test room creation fails with negative price."""
    repo = MockRoomRepository()
    use_case = CreateRoomUseCase(repo)

    dto = CreateRoomDTO(
        hotel_id=uuid4(),
        name="Room 1",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("-10.00"),
        capacity=1,
        beds="1 Single",
        size=20.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )

    with pytest.raises(ValueError, match="Price must be non-negative"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_create_room_invalid_capacity():
    """Test room creation fails with invalid capacity."""
    repo = MockRoomRepository()
    use_case = CreateRoomUseCase(repo)

    dto = CreateRoomDTO(
        hotel_id=uuid4(),
        name="Room 1",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("50.00"),
        capacity=0,
        beds="1 Single",
        size=20.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )

    with pytest.raises(ValueError, match="Capacity must be at least 1"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_create_room_invalid_size():
    """Test room creation fails with invalid size."""
    repo = MockRoomRepository()
    use_case = CreateRoomUseCase(repo)

    dto = CreateRoomDTO(
        hotel_id=uuid4(),
        name="Room 1",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("50.00"),
        capacity=1,
        beds="1 Single",
        size=0.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )

    with pytest.raises(ValueError, match="Size must be positive"):
        await use_case.execute(dto)


@pytest.mark.asyncio
async def test_get_room_success():
    """Test getting a room by ID."""
    repo = MockRoomRepository()
    use_case = GetRoomUseCase(repo)

    room_id = uuid4()
    room = Room(
        id=room_id,
        name="Room 101",
        room_type=RoomType.DOBLE,
        price=Decimal("100.00"),
        capacity=2,
        beds="2 Single",
        size=30.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi, TV",
    )
    repo.rooms[room_id] = room

    result = await use_case.execute(room_id)

    assert result.id == room_id
    assert result.name == "Room 101"


@pytest.mark.asyncio
async def test_get_room_not_found():
    """Test get room fails when room doesn't exist."""
    repo = MockRoomRepository()
    use_case = GetRoomUseCase(repo)

    with pytest.raises(ValueError, match="not found"):
        await use_case.execute(uuid4())


@pytest.mark.asyncio
async def test_list_rooms():
    """Test listing all rooms."""
    repo = MockRoomRepository()
    use_case = ListRoomsUseCase(repo)

    room1 = Room(
        name="Room 1",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("50.00"),
        capacity=1,
        beds="1 Single",
        size=20.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )
    room2 = Room(
        name="Room 2",
        room_type=RoomType.DOBLE,
        price=Decimal("80.00"),
        capacity=2,
        beds="1 Double",
        size=25.0,
        status=RoomStatus.OCUPADA,
        amenities="WiFi, TV",
    )
    repo.rooms[room1.id] = room1
    repo.rooms[room2.id] = room2

    result = await use_case.execute()

    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_room_stats():
    """Test getting room statistics."""
    repo = MockRoomRepository()
    use_case = GetRoomStatsUseCase(repo)

    room1 = Room(
        name="Room 1",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("50.00"),
        capacity=1,
        beds="1 Single",
        size=20.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )
    room2 = Room(
        name="Room 2",
        room_type=RoomType.DOBLE,
        price=Decimal("80.00"),
        capacity=2,
        beds="1 Double",
        size=25.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi, TV",
    )
    room3 = Room(
        name="Room 3",
        room_type=RoomType.SUITE,
        price=Decimal("150.00"),
        capacity=4,
        beds="1 King",
        size=45.0,
        status=RoomStatus.OCUPADA,
        amenities="WiFi, TV, Minibar",
    )
    repo.rooms[room1.id] = room1
    repo.rooms[room2.id] = room2
    repo.rooms[room3.id] = room3

    result = await use_case.execute()

    assert result.total == 3
    assert result.disponibles == 2
    assert result.ocupadas == 1
    assert result.mantenimiento == 0


def test_room_mark_available():
    """Test marking room as available."""
    room = Room(
        name="Room 1",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("50.00"),
        capacity=1,
        beds="1 Single",
        size=20.0,
        status=RoomStatus.OCUPADA,
        amenities="WiFi",
    )

    room.mark_available()

    assert room.status == RoomStatus.DISPONIBLE


def test_room_mark_occupied():
    """Test marking room as occupied."""
    room = Room(
        name="Room 1",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("50.00"),
        capacity=1,
        beds="1 Single",
        size=20.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )

    room.mark_occupied()

    assert room.status == RoomStatus.OCUPADA


def test_room_mark_maintenance():
    """Test marking room for maintenance."""
    room = Room(
        name="Room 1",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("50.00"),
        capacity=1,
        beds="1 Single",
        size=20.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )

    room.mark_maintenance()

    assert room.status == RoomStatus.MANTENIMIENTO


def test_room_is_available():
    """Test checking if room is available."""
    room = Room(
        name="Room 1",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("50.00"),
        capacity=1,
        beds="1 Single",
        size=20.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )

    assert room.is_available() is True

    room.mark_occupied()
    assert room.is_available() is False


@pytest.mark.asyncio
async def test_delete_room_success():
    """Test successful room deletion."""
    repo = MockRoomRepository()
    use_case = DeleteRoomUseCase(repo)

    room_id = uuid4()
    room = Room(
        id=room_id,
        name="Room 1",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("50.00"),
        capacity=1,
        beds="1 Single",
        size=20.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )
    repo.rooms[room_id] = room

    await use_case.execute(room_id)

    assert room_id not in repo.rooms


@pytest.mark.asyncio
async def test_delete_room_not_found():
    """Test delete fails when room doesn't exist."""
    repo = MockRoomRepository()
    use_case = DeleteRoomUseCase(repo)

    with pytest.raises(ValueError, match="not found"):
        await use_case.execute(uuid4())


@pytest.mark.asyncio
async def test_update_room_success():
    """Test successful room update."""
    repo = MockRoomRepository()
    use_case = UpdateRoomUseCase(repo)

    room_id = uuid4()
    room = Room(
        id=room_id,
        name="Room 101",
        room_type=RoomType.INDIVIDUAL,
        price=Decimal("100.00"),
        capacity=2,
        beds="1 Double",
        size=25.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )
    repo.rooms[room_id] = room

    dto = UpdateRoomDTO(name="Room 101 Updated", price=Decimal("120.00"))
    result = await use_case.execute(room_id, dto)

    assert result.name == "Room 101 Updated"
    assert result.price == Decimal("120.00")
    assert result.capacity == 2  # unchanged


@pytest.mark.asyncio
async def test_update_room_not_found():
    """Test update fails when room doesn't exist."""
    repo = MockRoomRepository()
    use_case = UpdateRoomUseCase(repo)

    with pytest.raises(ValueError, match="not found"):
        await use_case.execute(uuid4(), UpdateRoomDTO(name="New Name"))


@pytest.mark.asyncio
async def test_update_room_partial_fields():
    """Test that only provided fields are updated."""
    repo = MockRoomRepository()
    use_case = UpdateRoomUseCase(repo)

    room_id = uuid4()
    room = Room(
        id=room_id,
        name="Original",
        room_type=RoomType.DOBLE,
        price=Decimal("80.00"),
        capacity=2,
        beds="2 Single",
        size=30.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi, TV",
    )
    repo.rooms[room_id] = room

    dto = UpdateRoomDTO(status=RoomStatus.MANTENIMIENTO)
    result = await use_case.execute(room_id, dto)

    assert result.status == RoomStatus.MANTENIMIENTO
    assert result.name == "Original"  # unchanged
    assert result.price == Decimal("80.00")  # unchanged
