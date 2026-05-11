import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID

import aioboto3

from src.application.use_cases.update_room_availability import UpdateRoomAvailabilityUseCase
from src.infrastructure.config.settings import settings
from src.infrastructure.database.base import AsyncSessionLocal
from src.infrastructure.database.repositories.sqlalchemy_room_repository import (
    SQLAlchemyRoomRepository,
)

logger = logging.getLogger(__name__)

_POLL_WAIT_SECONDS = 20   # SQS long-poll (max 20s); reduces empty-receive API calls
_MAX_MESSAGES = 10
_VISIBILITY_TIMEOUT = 60  # seconds — must be >= max processing time per message


def _unwrap_sns_envelope(sqs_body: str) -> dict:
    """SNS fan-out wraps the payload in a Notification envelope.

    Transparently handles both SNS-wrapped and raw SQS messages so the
    queue can also be used for local testing without LocalStack.
    """
    outer = json.loads(sqs_body)
    if outer.get("Type") == "Notification":
        return json.loads(outer["Message"])
    return outer


async def _process_message(event: dict) -> None:
    trace_id = event.get("trace_id", "unknown")
    room_id_str = event.get("room_id")
    booking_status = event.get("status")
    start_time_str = event.get("start_time")
    end_time_str = event.get("end_time")
    booking_id = event.get("booking_id", "unknown")
    event_type = event.get("event_type", "unknown")

    logger.info(
        "sqs_message_received event_type=%s booking_id=%s room_id=%s status=%s trace_id=%s",
        event_type,
        booking_id,
        room_id_str,
        booking_status,
        trace_id,
    )

    if not all([room_id_str, booking_status, start_time_str, end_time_str]):
        logger.error(
            "sqs_message_malformed trace_id=%s event=%s",
            trace_id,
            event,
        )
        return

    room_id = UUID(room_id_str)
    start_time = datetime.fromisoformat(start_time_str)
    end_time = datetime.fromisoformat(end_time_str)

    async with AsyncSessionLocal() as session:
        try:
            repo = SQLAlchemyRoomRepository(session)
            use_case = UpdateRoomAvailabilityUseCase(repo)
            await use_case.execute(room_id, booking_status, start_time, end_time, trace_id=trace_id)
            await session.commit()
            logger.info(
                "sqs_message_processed event_type=%s booking_id=%s room_id=%s trace_id=%s",
                event_type,
                booking_id,
                room_id_str,
                trace_id,
            )
        except Exception as exc:
            await session.rollback()
            logger.error(
                "sqs_processing_error room_id=%s booking_id=%s trace_id=%s error=%s",
                room_id_str,
                booking_id,
                trace_id,
                exc,
            )
            raise  # re-raise so the message is NOT deleted and retries via visibility timeout


async def poll_sqs_loop() -> None:
    """Infinite long-poll loop. Launched as an asyncio background task in lifespan."""
    queue_url = settings.SQS_QUEUE_URL
    if not queue_url:
        logger.warning("sqs_consumer_disabled SQS_QUEUE_URL not configured")
        return

    logger.info("sqs_consumer_started queue_url=%s", queue_url)
    session = aioboto3.Session()

    async with session.client("sqs", region_name=settings.AWS_REGION) as sqs:
        while True:
            try:
                response = await sqs.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=_MAX_MESSAGES,
                    WaitTimeSeconds=_POLL_WAIT_SECONDS,
                    VisibilityTimeout=_VISIBILITY_TIMEOUT,
                )
                for msg in response.get("Messages", []):
                    receipt_handle = msg["ReceiptHandle"]
                    msg_id = msg.get("MessageId", "unknown")
                    trace_id = "unknown"
                    try:
                        event = _unwrap_sns_envelope(msg["Body"])
                        trace_id = event.get("trace_id", "unknown")
                        logger.info(
                            "sqs_message_dequeued message_id=%s trace_id=%s",
                            msg_id,
                            trace_id,
                        )
                        await _process_message(event)
                        await sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=receipt_handle,
                        )
                        logger.info(
                            "sqs_message_deleted message_id=%s trace_id=%s",
                            msg_id,
                            trace_id,
                        )
                    except Exception as exc:
                        logger.error(
                            "sqs_message_failed message_id=%s trace_id=%s error=%s",
                            msg_id,
                            trace_id,
                            exc,
                        )
                        # message reappears after VisibilityTimeout; goes to DLQ after max_receive_count
            except asyncio.CancelledError:
                logger.info("sqs_consumer_stopping")
                raise
            except Exception as exc:
                logger.error("sqs_poll_error error=%s — retrying in 5s", exc)
                await asyncio.sleep(5)
