from uuid import UUID

from src.domain.repositories.rate_repository_port import RateRepositoryPort


class DeleteRateUseCase:
    def __init__(self, repo: RateRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, rate_id: UUID) -> None:
        deleted = await self._repo.delete(rate_id)
        if not deleted:
            raise ValueError(f"Rate {rate_id} not found")
