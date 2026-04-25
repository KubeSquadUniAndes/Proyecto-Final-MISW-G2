from datetime import datetime, timezone
from uuid import UUID

from src.application.dtos.rate_dto import DiscountResponseDTO, UpdateDiscountDTO
from src.domain.repositories.discount_repository_port import DiscountRepositoryPort
from src.domain.repositories.rate_repository_port import RateRepositoryPort


class UpdateDiscountUseCase:
    def __init__(
        self,
        rate_repo: RateRepositoryPort,
        discount_repo: DiscountRepositoryPort,
    ) -> None:
        self._rate_repo = rate_repo
        self._discount_repo = discount_repo

    async def execute(
        self, discount_id: UUID, dto: UpdateDiscountDTO
    ) -> DiscountResponseDTO:
        discount = await self._discount_repo.get_by_id(discount_id)
        if not discount:
            raise ValueError(f"Discount {discount_id} not found")

        if dto.name is not None:
            discount.name = dto.name
        if dto.discount_type is not None:
            discount.discount_type = dto.discount_type
        if dto.value is not None:
            if dto.value <= 0:
                raise ValueError("Discount value must be positive")
            discount.value = dto.value
        if dto.start_date is not None:
            discount.start_date = dto.start_date
        if dto.end_date is not None:
            discount.end_date = dto.end_date

        if discount.start_date > discount.end_date:
            raise ValueError("start_date must be before or equal to end_date")

        rate = await self._rate_repo.get_by_id(discount.rate_id)
        if rate:
            final = discount.apply(rate.base_price)
            if final <= 0:
                raise ValueError("Discount would result in a price of zero or less")

        discount.updated_at = datetime.now(timezone.utc)
        updated = await self._discount_repo.update(discount)

        return DiscountResponseDTO(
            id=updated.id,
            rate_id=updated.rate_id,
            name=updated.name,
            discount_type=updated.discount_type,
            value=updated.value,
            start_date=updated.start_date,
            end_date=updated.end_date,
            is_active=updated.is_active(),
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
