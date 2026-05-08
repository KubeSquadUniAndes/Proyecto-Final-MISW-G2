import logging
import os

from src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

_firebase_initialized = False


def _init_firebase() -> bool:
    global _firebase_initialized  # noqa: PLW0603
    if _firebase_initialized:
        return True
    try:
        import firebase_admin
        from firebase_admin import credentials

        path = settings.FIREBASE_SERVICE_ACCOUNT_PATH
        if not os.path.exists(path):
            logger.warning(
                "fcm_not_configured — service account file not found: %s", path
            )
            return False
        cred = credentials.Certificate(path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        return True
    except Exception as exc:
        logger.error("fcm_init_error error=%s", exc)
        return False


async def send_fcm(
    fcm_token: str, title: str, body: str, data: dict | None = None
) -> bool:
    """Sends a push notification via Firebase FCM. Returns True on success."""
    if not fcm_token:
        logger.warning("fcm_skipped — no token provided")
        return False

    if not _init_firebase():
        return False

    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    sound="default",
                    priority="high",
                ),
            ),
        )
        response = messaging.send(message)
        logger.info("fcm_sent token=%s... message_id=%s", fcm_token[:20], response)
        return True
    except Exception as exc:
        logger.error("fcm_error token=%s... error=%s", fcm_token[:20], exc)
        return False
