from src.application.dtos.rate_dto import CreateRateDTO, DiscountResponseDTO, RateResponseDTO
from src.domain.entities.rate import Rate
from src.domain.repositories.rate_repository_port import RateRepositoryPort


class CreateRateUseCase:
    def __init__(self, repo: RateRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, dto: CreateRateDTO) -> RateResponseDTO:
        if dto.base_price <= 0:
            raise ValueError("Base price must be positive")

        existing = await self._repo.get_by_hotel_room_type_season(
            dto.hotel_id, dto.room_type, dto.season
        )
        if existing:
            raise ValueError(
                f"Rate for {dto.room_type} / {dto.season} already exists"
            )

        rate = Rate(
            hotel_id=dto.hotel_id,
            room_type=dto.room_type,
            season=dto.season,
            base_price=dto.base_price,
        )
        saved = await self._repo.save(rate)

        return RateResponseDTO(
            id=saved.id,
            hotel_id=saved.hotel_id,
            room_type=saved.room_type,
            season=saved.season,
            base_price=saved.base_price,
            final_price=saved.base_price,
            active_discount=None,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )
