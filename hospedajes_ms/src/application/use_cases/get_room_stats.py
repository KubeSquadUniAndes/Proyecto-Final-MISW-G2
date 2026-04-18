from src.application.dtos.room_dto import RoomStatsDTO
from src.domain.entities.room import RoomStatus
from src.domain.repositories.room_repository_port import RoomRepositoryPort


class GetRoomStatsUseCase:
    def __init__(self, room_repo: RoomRepositoryPort) -> None:
        self._repo = room_repo

    async def execute(self) -> RoomStatsDTO:
        total = await self._repo.count_total()
        disponibles = await self._repo.count_by_status(RoomStatus.DISPONIBLE)
        ocupadas = await self._repo.count_by_status(RoomStatus.OCUPADA)
        mantenimiento = await self._repo.count_by_status(RoomStatus.MANTENIMIENTO)
        return RoomStatsDTO(
            total=total,
            disponibles=disponibles,
            ocupadas=ocupadas,
            mantenimiento=mantenimiento,
        )
