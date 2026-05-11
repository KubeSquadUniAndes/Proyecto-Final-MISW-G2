from abc import ABC, abstractmethod

from src.domain.events.room_availability_event import RoomAvailabilityEvent


class RoomAvailabilityPublisherPort(ABC):
    @abstractmethod
    async def publish(self, event: RoomAvailabilityEvent) -> None:
        """Publish a room availability event. Implementations must never raise."""
        ...
