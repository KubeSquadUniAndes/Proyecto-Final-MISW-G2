from uuid import UUID

from src.application.dtos.rate_dto import DiscountResponseDTO, RateResponseDTO
from src.domain.repositories.discount_repository_port import DiscountRepositoryPort
from src.domain.repositories.rate_repository_port import RateRepositoryPort


class GetRateUseCase:
    def __init__(
        self,
        rate_repo: RateRepositoryPort,
        discount_repo: DiscountRepositoryPort,
    ) -> None:
        self._rate_repo = rate_repo
        self._discount_repo = discount_repo

    async def execute(self, rate_id: UUID) -> RateResponseDTO:
        rate = await self._rate_repo.get_by_id(rate_id)
        if not rate:
            raise ValueError(f"Rate {rate_id} not found")

        discounts = await self._discount_repo.list_by_rate(rate_id)
        final_price, active = rate.effective_price(discounts)

        active_dto = None
        if active:
            active_dto = DiscountResponseDTO(
                id=active.id,
                rate_id=active.rate_id,
                name=active.name,
                discount_type=active.discount_type,
                value=active.value,
                start_date=active.start_date,
                end_date=active.end_date,
                is_active=True,
                created_at=active.created_at,
                updated_at=active.updated_at,
            )

        return RateResponseDTO(
            id=rate.id,
            hotel_id=rate.hotel_id,
            room_type=rate.room_type,
            season=rate.season,
            base_price=rate.base_price,
            final_price=final_price,
            active_discount=active_dto,
            created_at=rate.created_at,
            updated_at=rate.updated_at,
        )
