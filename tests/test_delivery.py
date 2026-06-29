from uuid import uuid4

import respx
from httpx import Response

from app.adapters.inbound.messaging.schemas import PaymentNotificationMessage
from app.application.use_cases.deliver_payment_notification import (
    DeliverPaymentNotificationUseCase,
)
from app.infrastructure.gateways.http_webhook_client import HttpWebhookClient


def create_notification() -> PaymentNotificationMessage:
    transaction_id = uuid4()
    return PaymentNotificationMessage.model_validate(
        {
            "event_id": str(uuid4()),
            "event_type": "payment.notification_requested",
            "schema_version": 1,
            "occurred_at": "2026-06-28T12:00:00Z",
            "correlation_id": str(transaction_id),
            "transaction_id": str(transaction_id),
            "provider_transaction_id": f"mock_{transaction_id}",
            "status": "APPROVED",
            "message": "Approved",
            "notification_url": "https://merchant.example/webhooks/payments",
        }
    )


@respx.mock
def test_delivery_posts_public_contract_and_idempotency_headers():
    route = respx.post("https://merchant.example/webhooks/payments").mock(
        return_value=Response(204)
    )
    notification = create_notification()

    webhook_client = HttpWebhookClient(timeout_seconds=2)
    use_case = DeliverPaymentNotificationUseCase(webhook_client)
    use_case.execute(notification.to_command())

    request = route.calls[0].request
    body = request.content.decode()
    assert '"event_type":"payment.status_changed"' in body
    assert "notification_url" not in body
    assert request.headers["Idempotency-Key"] == str(notification.event_id)
    assert request.headers["X-OnyxPay-Event-Id"] == str(notification.event_id)
