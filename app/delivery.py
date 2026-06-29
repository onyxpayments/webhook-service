import httpx

from app.schemas import PaymentNotificationMessage


class WebhookDelivery:
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds

    def deliver(self, notification: PaymentNotificationMessage) -> None:
        event_id = str(notification.event_id)
        response = httpx.post(
            str(notification.notification_url),
            json=notification.delivery_payload(),
            headers={
                "X-OnyxPay-Event-Id": event_id,
                "Idempotency-Key": event_id,
                "User-Agent": "OnyxPay-Webhook/1.0",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
