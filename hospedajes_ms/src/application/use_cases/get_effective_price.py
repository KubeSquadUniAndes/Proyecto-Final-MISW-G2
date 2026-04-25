from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.domain.entities.rate import SeasonType
from src.domain.entities.room import RoomType
from src.domain.repositories.discount_repository_port import DiscountRepositoryPort
from src.domain.repositories.rate_repository_port import RateRepositoryPort
from src.domain.repositories.room_repository_port import RoomRepositoryPort


@dataclass
class EffectivePriceResult:
    room_type: RoomType
    season: SeasonType | None
    base_price: Decimal
    final_price: Decimal
    has_discount: bool
    discount_name: str | None


class GetEffectivePriceUseCase:
    """
    Returns the effective price for a room_type in a hotel.
    Used by reservas_ms to determine the price at booking time.
    Fallback: room.price if no rate is configured.
    """

    def __init__(
        self,
        rate_repo: RateRepositoryPort,
        discount_repo: DiscountRepositoryPort,
        room_repo: RoomRepositoryPort,
    ) -> None:
        self._rate_repo = rate_repo
        self._discount_repo = discount_repo
        self._room_repo = room_repo

    async def execute(
        self,
        hotel_id: UUID,
        room_type: RoomType,
        season: SeasonType = SeasonType.BASE,
    ) -> EffectivePriceResult:
        rate = await self._rate_repo.get_by_hotel_room_type_season(
            hotel_id, room_type, season
        )

        if not rate:
            rooms = await self._room_repo.list_all(hotel_id=hotel_id)
            fallback = next((r for r in rooms if r.room_type == room_type), None)
            fallback_price = fallback.price if fallback else Decimal("0")
            return EffectivePriceResult(
                room_type=room_type,
                season=None,
                base_price=fallback_price,
                final_price=fallback_price,
                has_discount=False,
                discount_name=None,
            )

        discounts = await self._discount_repo.list_by_rate(rate.id)
        final_price, active = rate.effective_price(discounts)

        return EffectivePriceResult(
            room_type=room_type,
            season=rate.season,
            base_price=rate.base_price,
            final_price=final_price,
            has_discount=active is not None,
            discount_name=active.name if active else None,
        )
