from uuid import UUID

from src.application.dtos.rate_dto import DiscountResponseDTO
from src.domain.repositories.discount_repository_port import DiscountRepositoryPort


class ListDiscountsUseCase:
    def __init__(self, repo: DiscountRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, rate_id: UUID) -> list[DiscountResponseDTO]:
        discounts = await self._repo.list_by_rate(rate_id)
        return [
            DiscountResponseDTO(
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
            for d in discounts
        ]
