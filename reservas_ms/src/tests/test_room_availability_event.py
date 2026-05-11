"""Tests for RoomAvailabilityEvent and RoomAvailabilityPublisherPort."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from src.domain.events.room_availability_event import RoomAvailabilityEvent
from src.domain.ports.room_availability_publisher_port import RoomAvailabilityPublisherPort


def _make_event(**kwargs) -> RoomAvailabilityEvent:
    now = datetime.now(timezone.utc)
    defaults = dict(
        event_type="booking_created",
        booking_id=uuid4(),
        room_id=uuid4(),
        hotel_id=uuid4(),
        status="pending",
        start_time=now,
        end_time=now + timedelta(days=3),
    )
    defaults.update(kwargs)
    return RoomAvailabilityEvent(**defaults)


def test_room_availability_event_creation():
    event = _make_event()
    assert event.event_type == "booking_created"
    assert event.status == "pending"
    assert event.trace_id is not None
    assert event.published_at is not None


def test_room_availability_event_to_dict():
    booking_id = uuid4()
    room_id = uuid4()
    hotel_id = uuid4()
    event = _make_event(
        event_type="booking_updated",
        booking_id=booking_id,
        room_id=room_id,
        hotel_id=hotel_id,
        status="confirmed",
    )
    d = event.to_dict()
    assert d["event_type"] == "booking_updated"
    assert d["booking_id"] == str(booking_id)
    assert d["room_id"] == str(room_id)
    assert d["hotel_id"] == str(hotel_id)
    assert d["status"] == "confirmed"
    assert "trace_id" in d
    assert "published_at" in d
    assert "start_time" in d
    assert "end_time" in d


def test_room_availability_publisher_port_is_abstract():
    with pytest.raises(TypeError):
        RoomAvailabilityPublisherPort()  # type: ignore[abstract]


def test_room_availability_publisher_port_concrete_implementation():
    class ConcretePublisher(RoomAvailabilityPublisherPort):
        async def publish(self, event: RoomAvailabilityEvent) -> None:
            pass

    publisher = ConcretePublisher()
    assert isinstance(publisher, RoomAvailabilityPublisherPort)
