from app.application.use_cases.deliver_payment_notification import (
    DeliverPaymentNotificationUseCase,
)
from app.infrastructure.gateways.http_webhook_client import HttpWebhookClient
from config.settings import settings


def get_deliver_payment_notification_use_case() -> DeliverPaymentNotificationUseCase:
    return DeliverPaymentNotificationUseCase(
        webhook_client=HttpWebhookClient(
            timeout_seconds=settings.webhook_timeout_seconds,
        )
    )
