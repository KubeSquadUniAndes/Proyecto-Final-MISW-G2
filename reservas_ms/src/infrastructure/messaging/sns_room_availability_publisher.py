import json
import logging

import aioboto3

from src.domain.events.room_availability_event import RoomAvailabilityEvent
from src.domain.ports.room_availability_publisher_port import (
    RoomAvailabilityPublisherPort,
)

logger = logging.getLogger(__name__)


class SNSRoomAvailabilityPublisher(RoomAvailabilityPublisherPort):
    """Infrastructure adapter: publishes booking events to AWS SNS.

    Never raises — failures are logged and swallowed so the booking flow
    is never blocked by a messaging outage.
    """

    def __init__(self, topic_arn: str, aws_region: str) -> None:
        self._topic_arn = topic_arn
        self._aws_region = aws_region

    async def publish(self, event: RoomAvailabilityEvent) -> None:
        if not self._topic_arn:
            return

        message_body = json.dumps(event.to_dict())
        logger.info(
            "sns_publish_attempt event_type=%s booking_id=%s room_id=%s hotel_id=%s status=%s trace_id=%s",
            event.event_type,
            event.booking_id,
            event.room_id,
            event.hotel_id,
            event.status,
            event.trace_id,
        )
        try:
            session = aioboto3.Session()
            async with session.client("sns", region_name=self._aws_region) as sns:
                response = await sns.publish(
                    TopicArn=self._topic_arn,
                    Message=message_body,
                    MessageAttributes={
                        "event_type": {
                            "DataType": "String",
                            "StringValue": event.event_type,
                        },
                        "trace_id": {
                            "DataType": "String",
                            "StringValue": event.trace_id,
                        },
                    },
                )
            logger.info(
                "sns_published event_type=%s booking_id=%s room_id=%s hotel_id=%s status=%s trace_id=%s message_id=%s",
                event.event_type,
                event.booking_id,
                event.room_id,
                event.hotel_id,
                event.status,
                event.trace_id,
                response.get("MessageId", "unknown"),
            )
        except Exception as exc:
            logger.error(
                "sns_publish_failed event_type=%s booking_id=%s trace_id=%s error=%s",
                event.event_type,
                event.booking_id,
                event.trace_id,
                exc,
            )
