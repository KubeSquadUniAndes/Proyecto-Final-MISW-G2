import logging

from src.application.dtos.analysis_dto import AnalysisResultDTO, AnalyzeBookingDTO, AnomalyEventDTO
from src.domain.entities.booking_analysis import BookingAnalysisRequest
from src.domain.repositories.anomaly_event_repository_port import AnomalyEventRepositoryPort
from src.domain.repositories.notification_port import NotificationPort
from src.domain.services.anomaly_detector_service import AnomalyDetectorService

logger = logging.getLogger(__name__)


class AnalyzeBookingUseCase:
    """Input port: receives a booking, runs anomaly detection, and triggers actions.

    Flow:
    1. Run anomaly detection (random + heuristic rules)
    2. If anomalous:
       a. Persist all AnomalyEvent records
       b. Call login_handler_ms → block user + revoke sessions
       c. Send security alert email
       d. Log security entry
    3. Return analysis result (booking is rejected if anomalous)
    """

    def __init__(
        self,
        detector: AnomalyDetectorService,
        anomaly_repo: AnomalyEventRepositoryPort,
        notification: NotificationPort,
    ) -> None:
        self._detector = detector
        self._anomaly_repo = anomaly_repo
        self._notification = notification

    async def execute(self, dto: AnalyzeBookingDTO) -> AnalysisResultDTO:
        request = BookingAnalysisRequest(
            user_id=dto.user_id,
            booking_id=dto.booking_id,
            resource_id=dto.resource_id,
            start_time=dto.start_time,
            end_time=dto.end_time,
        )

        # ── Step 1: Detect anomalies ─────────────────────────────────────────
        events = await self._detector.analyze(request)
        is_anomalous = len(events) > 0
        action_taken = "none"

        if not is_anomalous:
            logger.info(
                "booking_analysis=clean user_id=%s booking_id=%s",
                dto.user_id, dto.booking_id,
            )
            return AnalysisResultDTO(
                booking_id=dto.booking_id,
                is_anomalous=False,
                anomaly_count=0,
                events=[],
                action_taken="none",
                message="Booking analysis passed. No anomalies detected.",
            )

        # ── Step 2a: Persist anomaly events ──────────────────────────────────
        saved_events = []
        for event in events:
            saved = await self._anomaly_repo.save(event)
            saved_events.append(saved)
            logger.warning(
                "anomaly_detected type=%s severity=%s score=%.2f "
                "user_id=%s booking_id=%s description=%r",
                event.anomaly_type, event.severity, event.score,
                event.user_id, event.booking_id, event.description,
            )

        # ── Step 2b: Block user via login_handler_ms ──────────────────────────
        reason = "; ".join(e.description for e in saved_events)
        block_success = await self._notification.block_user(dto.user_id, reason)
        if block_success:
            action_taken = "user_blocked"
            logger.warning(
                "user_blocked user_id=%s reason=%r", dto.user_id, reason
            )
        else:
            logger.error(
                "block_user_failed user_id=%s — login_handler_ms unreachable", dto.user_id
            )

        # ── Step 2c: Send security alert email ───────────────────────────────
        highest_severity_event = max(saved_events, key=lambda e: e.score)
        email_sent = await self._notification.send_security_alert_email(highest_severity_event)
        if email_sent:
            action_taken = "user_blocked_and_alerted" if block_success else "alert_sent"
            logger.info("security_alert_email_sent user_id=%s", dto.user_id)
        else:
            logger.error("security_alert_email_failed user_id=%s", dto.user_id)

        return AnalysisResultDTO(
            booking_id=dto.booking_id,
            is_anomalous=True,
            anomaly_count=len(saved_events),
            events=[AnomalyEventDTO(
                id=e.id,
                user_id=e.user_id,
                booking_id=e.booking_id,
                anomaly_type=e.anomaly_type,
                severity=e.severity,
                score=e.score,
                description=e.description,
                created_at=e.created_at,
            ) for e in saved_events],
            action_taken=action_taken,
            message=(
                f"Anomaly detected ({len(saved_events)} rule(s) triggered). "
                "User has been blocked and a security alert has been sent."
            ),
        )
