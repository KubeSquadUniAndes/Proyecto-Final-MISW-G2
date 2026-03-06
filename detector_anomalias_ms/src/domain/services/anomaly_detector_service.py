import random
from datetime import datetime, timedelta

from src.domain.entities.anomaly_event import AnomalyEvent, AnomalyType, AnomalySeverity
from src.domain.entities.booking_analysis import BookingAnalysisRequest
from src.domain.repositories.booking_history_repository_port import BookingHistoryRepositoryPort


# ── Thresholds (all tunable via config) ──────────────────────────────────────
DEFAULT_RANDOM_ANOMALY_RATE = 0.30        # 30% of requests flagged randomly (for testing)
MAX_BOOKINGS_PER_WINDOW = 5               # more than N bookings in the window → suspicious
MAX_DISTINCT_RESOURCES_PER_WINDOW = 4     # more than N different resources → suspicious
FREQUENCY_WINDOW_HOURS = 1               # sliding window for frequency checks
MIN_DURATION_MINUTES = 15                # shorter than this → unusual
MAX_DURATION_MINUTES = 480               # longer than this → unusual (8 hours)


class AnomalyDetectorService:
    """Domain service: classifies a booking request as normal or anomalous.

    Uses a combination of:
    1. Configurable random sampling (for testing / controlled experiments).
    2. Heuristic rules on 3 features:
       - High booking frequency in a time window
       - Unusual booking duration
       - Many different resources in a time window
    Each rule contributes a score; the final score is a weighted average.
    """

    def __init__(
        self,
        booking_history_repo: BookingHistoryRepositoryPort,
        random_anomaly_rate: float = DEFAULT_RANDOM_ANOMALY_RATE,
    ) -> None:
        self._history = booking_history_repo
        self._random_rate = random_anomaly_rate

    async def analyze(self, request: BookingAnalysisRequest) -> list[AnomalyEvent]:
        """Returns a list of AnomalyEvents (empty = no anomaly detected)."""
        events: list[AnomalyEvent] = []
        since = datetime.utcnow() - timedelta(hours=FREQUENCY_WINDOW_HOURS)

        # ── 1. Random sampling trigger (for testing) ─────────────────────────
        if random.random() < self._random_rate:
            events.append(AnomalyEvent(
                user_id=request.user_id,
                booking_id=request.booking_id,
                anomaly_type=AnomalyType.RANDOM_SAMPLE,
                severity=AnomalySeverity.MEDIUM,
                score=round(random.uniform(0.6, 0.9), 2),
                description=(
                    f"Random sampling triggered anomaly flag "
                    f"(rate={self._random_rate:.0%}). "
                    "Used for controlled experiment validation."
                ),
            ))

        # ── 2. High frequency check ───────────────────────────────────────────
        recent_count = await self._history.count_recent_bookings(request.user_id, since)
        if recent_count >= MAX_BOOKINGS_PER_WINDOW:
            score = min(1.0, recent_count / (MAX_BOOKINGS_PER_WINDOW * 2))
            severity = AnomalySeverity.HIGH if score >= 0.8 else AnomalySeverity.MEDIUM
            events.append(AnomalyEvent(
                user_id=request.user_id,
                booking_id=request.booking_id,
                anomaly_type=AnomalyType.HIGH_FREQUENCY,
                severity=severity,
                score=round(score, 2),
                description=(
                    f"User made {recent_count} bookings in the last "
                    f"{FREQUENCY_WINDOW_HOURS}h (threshold: {MAX_BOOKINGS_PER_WINDOW})."
                ),
            ))

        # ── 3. Unusual duration check ─────────────────────────────────────────
        duration = request.duration_minutes
        if duration < MIN_DURATION_MINUTES or duration > MAX_DURATION_MINUTES:
            if duration < MIN_DURATION_MINUTES:
                score = round(1.0 - duration / MIN_DURATION_MINUTES, 2)
                detail = f"Duration {duration:.0f}min is below minimum {MIN_DURATION_MINUTES}min."
            else:
                score = min(1.0, round(duration / MAX_DURATION_MINUTES - 1.0, 2))
                detail = f"Duration {duration:.0f}min exceeds maximum {MAX_DURATION_MINUTES}min."

            severity = AnomalySeverity.HIGH if score >= 0.8 else AnomalySeverity.LOW
            events.append(AnomalyEvent(
                user_id=request.user_id,
                booking_id=request.booking_id,
                anomaly_type=AnomalyType.UNUSUAL_DURATION,
                severity=severity,
                score=max(0.0, min(1.0, score)),
                description=detail,
            ))

        # ── 4. Multi-resource check ───────────────────────────────────────────
        distinct_resources = await self._history.count_distinct_resources(request.user_id, since)
        if distinct_resources >= MAX_DISTINCT_RESOURCES_PER_WINDOW:
            score = min(1.0, distinct_resources / (MAX_DISTINCT_RESOURCES_PER_WINDOW * 2))
            severity = AnomalySeverity.HIGH if score >= 0.8 else AnomalySeverity.MEDIUM
            events.append(AnomalyEvent(
                user_id=request.user_id,
                booking_id=request.booking_id,
                anomaly_type=AnomalyType.MULTI_RESOURCE,
                severity=severity,
                score=round(score, 2),
                description=(
                    f"User booked {distinct_resources} different resources in the last "
                    f"{FREQUENCY_WINDOW_HOURS}h (threshold: {MAX_DISTINCT_RESOURCES_PER_WINDOW})."
                ),
            ))

        return events
