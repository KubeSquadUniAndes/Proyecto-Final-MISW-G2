from uuid import UUID

from src.application.dtos.rate_dto import DiscountResponseDTO, RateResponseDTO
from src.domain.entities.room import RoomType
from src.domain.repositories.discount_repository_port import DiscountRepositoryPort
from src.domain.repositories.rate_repository_port import RateRepositoryPort


def _discount_dto(d):
    return DiscountResponseDTO(
        id=d.id,
        rate_id=d.rate_id,
        name=d.name,
        discount_type=d.discount_type,
        value=d.value,
        start_date=d.start_date,
        end_date=d.end_date,
        is_active=d.is_active(),
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


class ListRatesUseCase:
    def __init__(
        self,
        rate_repo: RateRepositoryPort,
        discount_repo: DiscountRepositoryPort,
    ) -> None:
        self._rate_repo = rate_repo
        self._discount_repo = discount_repo

    async def execute(
        self, hotel_id: UUID, room_type: RoomType | None = None
    ) -> list[RateResponseDTO]:
        rates = await self._rate_repo.list_by_hotel(hotel_id, room_type)
        result = []
        for rate in rates:
            discounts = await self._discount_repo.list_by_rate(rate.id)
            final_price, active = rate.effective_price(discounts)
            result.append(
                RateResponseDTO(
                    id=rate.id,
                    hotel_id=rate.hotel_id,
                    room_type=rate.room_type,
                    season=rate.season,
                    base_price=rate.base_price,
                    final_price=final_price,
                    active_discount=_discount_dto(active) if active else None,
                    created_at=rate.created_at,
                    updated_at=rate.updated_at,
                )
            )
        return result
