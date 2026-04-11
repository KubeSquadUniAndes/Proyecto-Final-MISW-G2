from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.anomaly_event import AnomalyEvent


class AnomalyEventRepositoryPort(ABC):
    """Output port: persists and queries anomaly events."""

    @abstractmethod
    async def save(self, event: AnomalyEvent) -> AnomalyEvent: ...

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> list[AnomalyEvent]: ...

    @abstractmethod
    async def count_recent_by_user(self, user_id: UUID, since: object) -> int:
        """Returns number of anomaly events for a user after `since` datetime."""
        ...
