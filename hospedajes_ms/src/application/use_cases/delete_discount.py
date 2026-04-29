from uuid import UUID

from src.domain.repositories.discount_repository_port import DiscountRepositoryPort


class DeleteDiscountUseCase:
    def __init__(self, repo: DiscountRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, discount_id: UUID) -> None:
        deleted = await self._repo.delete(discount_id)
        if not deleted:
            raise ValueError(f"Discount {discount_id} not found")
