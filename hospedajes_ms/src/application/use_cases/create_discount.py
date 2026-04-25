from src.application.dtos.rate_dto import CreateDiscountDTO, DiscountResponseDTO
from src.domain.entities.rate import Discount
from src.domain.repositories.discount_repository_port import DiscountRepositoryPort
from src.domain.repositories.rate_repository_port import RateRepositoryPort


class CreateDiscountUseCase:
    def __init__(
        self,
        rate_repo: RateRepositoryPort,
        discount_repo: DiscountRepositoryPort,
    ) -> None:
        self._rate_repo = rate_repo
        self._discount_repo = discount_repo

    async def execute(self, dto: CreateDiscountDTO) -> DiscountResponseDTO:
        rate = await self._rate_repo.get_by_id(dto.rate_id)
        if not rate:
            raise ValueError(f"Rate {dto.rate_id} not found")

        if dto.start_date > dto.end_date:
            raise ValueError("start_date must be before or equal to end_date")
        if dto.value <= 0:
            raise ValueError("Discount value must be positive")

        discount = Discount(
            rate_id=dto.rate_id,
            name=dto.name,
            discount_type=dto.discount_type,
            value=dto.value,
            start_date=dto.start_date,
            end_date=dto.end_date,
        )

        final = discount.apply(rate.base_price)
        if final <= 0:
            raise ValueError("Discount would result in a price of zero or less")

        saved = await self._discount_repo.save(discount)
        return DiscountResponseDTO(
            id=saved.id,
            rate_id=saved.rate_id,
            name=saved.name,
            discount_type=saved.discount_type,
            value=saved.value,
            start_date=saved.start_date,
            end_date=saved.end_date,
            is_active=saved.is_active(),
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )
