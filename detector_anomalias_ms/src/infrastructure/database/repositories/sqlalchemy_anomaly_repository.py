from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.anomaly_event import AnomalyEvent, AnomalyType, AnomalySeverity
from src.domain.repositories.anomaly_event_repository_port import (
    AnomalyEventRepositoryPort,
)
from src.infrastructure.database.models.anomaly_event_model import AnomalyEventModel


class SQLAlchemyAnomalyEventRepository(AnomalyEventRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, m: AnomalyEventModel) -> AnomalyEvent:
        return AnomalyEvent(
            id=m.id,
            user_id=m.user_id,
            booking_id=m.booking_id,
            anomaly_type=AnomalyType(m.anomaly_type),
            severity=AnomalySeverity(m.severity),
            score=m.score,
            description=m.description,
            resolved=m.resolved,
            created_at=m.created_at,
        )

    async def save(self, event: AnomalyEvent) -> AnomalyEvent:
        model = AnomalyEventModel(
            id=event.id,
            user_id=event.user_id,
            booking_id=event.booking_id,
            anomaly_type=event.anomaly_type,
            severity=event.severity,
            score=event.score,
            description=event.description,
            resolved=event.resolved,
            created_at=event.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def list_by_user(self, user_id: UUID) -> list[AnomalyEvent]:
        result = await self._session.execute(
            select(AnomalyEventModel)
            .where(AnomalyEventModel.user_id == user_id)
            .order_by(AnomalyEventModel.created_at.desc())
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count_recent_by_user(self, user_id: UUID, since: datetime) -> int:
        result = await self._session.execute(
            select(func.count()).where(
                AnomalyEventModel.user_id == user_id,
                AnomalyEventModel.created_at >= since,
            )
        )
        return result.scalar_one()
