# notificaciones_ms

Simple notification microservice — receives anomaly alerts from `detector_anomalias_ms`
and dispatches them via **Email (SMTP)** and **Slack webhook**.

No database. No JWT. Just receives and sends.

---

## Structure

```
src/
├── main.py
├── application/
│   ├── dtos/
│   │   └── notification_dto.py         ← SendNotificationDTO, NotificationResultDTO
│   └── use_cases/
│       └── send_notification.py        ← Calls both channels, collects results
└── infrastructure/
    ├── config/
    │   └── settings.py                 ← SMTP + Slack + API key config
    ├── channels/
    │   ├── email_channel.py            ← SMTP adapter
    │   └── slack_channel.py            ← Slack webhook adapter
    └── http/
        ├── routes/
        │   ├── notification_router.py  ← POST /api/v1/notifications/alert
        │   └── health_router.py        ← GET /health
        └── schemas/
            └── notification_schema.py
```

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET`  | `/health` | — | Shows service status and channel config |
| `POST` | `/api/v1/notifications/alert` | `X-Api-Key` | Send anomaly alert via email + Slack |

---

## Quickstart

```bash
cp .env.example .env
# Fill in SMTP_USER, SMTP_PASSWORD, SLACK_WEBHOOK_URL

pip install -r requirements.txt
uvicorn src.main:app --reload --port 8003
```

---

## Usage example

```bash
curl -X POST http://localhost:8003/api/v1/notifications/alert \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: change-internal-key-in-production" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "booking_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "anomaly_type": "random_sample",
    "severity": "medium",
    "score": 0.73,
    "description": "Random sampling triggered anomaly flag",
    "detected_at": "2026-04-01T10:00:00"
  }'
```

**Response:**
```json
{ "email_sent": true, "slack_sent": true, "errors": [] }
```

---

## Channel behavior

- Both channels are always attempted independently — if one fails the other still runs.
- If `SMTP_USER` is empty → email is skipped (logged as warning, not error).
- If `SLACK_WEBHOOK_URL` is empty → Slack is skipped.
- `errors` in the response lists which channels failed or were not configured.

---

## Integrating with detector_anomalias_ms

In `detector_anomalias_ms/src/infrastructure/clients/notification_adapter.py`,
replace the `send_security_alert_email` method with a call to this service:

```python
async with httpx.AsyncClient(timeout=5.0) as client:
    await client.post(
        f"{NOTIFICACIONES_MS_URL}/api/v1/notifications/alert",
        json={
            "user_id": str(event.user_id),
            "booking_id": str(event.booking_id),
            "anomaly_type": event.anomaly_type.value,
            "severity": event.severity.value,
            "score": event.score,
            "description": event.description,
            "detected_at": event.created_at.isoformat(),
        },
        headers={"X-Api-Key": INTERNAL_API_KEY},
    )
```

---

## Tests

```bash
pytest tests/ -v --cov=src
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INTERNAL_API_KEY` | `change-internal-key` | Key used by `detector_anomalias_ms` |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server host |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USER` | — | SMTP username (leave blank to disable) |
| `SMTP_PASSWORD` | — | SMTP password |
| `EMAIL_FROM` | `alerts@experiment.local` | Sender address |
| `EMAIL_TO` | `security@experiment.local` | Recipient address |
| `SLACK_WEBHOOK_URL` | — | Slack incoming webhook URL (leave blank to disable) |
| `SLACK_CHANNEL` | `#security-alerts` | Slack channel name |
