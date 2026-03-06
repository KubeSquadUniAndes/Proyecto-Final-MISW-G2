from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.anomaly_event import AnomalyEvent


class NotificationPort(ABC):
    """Output port: sends anomaly alerts to external systems."""

    @abstractmethod
    async def block_user(self, user_id: UUID, reason: str) -> bool:
        """Calls login_handler_ms to block the user. Returns True on success."""
        ...

    @abstractmethod
    async def send_security_alert_email(self, event: AnomalyEvent) -> bool:
        """Sends a security alert email. Returns True on success."""
        ...
