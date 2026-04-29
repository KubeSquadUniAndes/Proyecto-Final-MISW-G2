from datetime import datetime, timezone
from uuid import UUID

from src.application.dtos.rate_dto import RateResponseDTO, UpdateRateDTO
from src.domain.repositories.rate_repository_port import RateRepositoryPort


class UpdateRateUseCase:
    def __init__(self, repo: RateRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, rate_id: UUID, dto: UpdateRateDTO) -> RateResponseDTO:
        rate = await self._repo.get_by_id(rate_id)
        if not rate:
            raise ValueError(f"Rate {rate_id} not found")
        if dto.base_price <= 0:
            raise ValueError("Base price must be positive")

        rate.base_price = dto.base_price
        rate.updated_at = datetime.now(timezone.utc)
        updated = await self._repo.update(rate)

        return RateResponseDTO(
            id=updated.id,
            hotel_id=updated.hotel_id,
            room_type=updated.room_type,
            season=updated.season,
            base_price=updated.base_price,
            final_price=updated.base_price,
            active_discount=None,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
