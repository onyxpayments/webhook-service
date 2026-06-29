import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pika

from app.adapters.inbound.messaging.payment_notification_consumer import (
    PaymentNotificationConsumer,
)
from config.settings import Settings


def create_body() -> bytes:
    transaction_id = uuid4()
    return json.dumps(
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
    ).encode()


def create_delivery(headers=None):
    channel = Mock()
    channel.basic_publish.return_value = True
    method = SimpleNamespace(delivery_tag=7)
    properties = pika.BasicProperties(
        content_type="application/json",
        delivery_mode=2,
        message_id=str(uuid4()),
        headers=headers or {},
    )
    return channel, method, properties


def create_consumer(use_case):
    return PaymentNotificationConsumer(
        Settings(_env_file=None),
        use_case_factory=lambda: use_case,
    )


def test_successful_delivery_acknowledges_message():
    channel, method, properties = create_delivery()
    use_case = Mock()

    create_consumer(use_case).handle_message(
        channel,
        method,
        properties,
        create_body(),
    )

    use_case.execute.assert_called_once()
    channel.basic_ack.assert_called_once_with(delivery_tag=7)


def test_failed_delivery_is_sent_to_retry_queue():
    channel, method, properties = create_delivery()
    use_case = Mock()
    use_case.execute.side_effect = RuntimeError("merchant unavailable")

    create_consumer(use_case).handle_message(
        channel,
        method,
        properties,
        create_body(),
    )

    published = channel.basic_publish.call_args.kwargs
    assert published["exchange"] == "webhook.retry"
    assert published["properties"].headers["x-retry-count"] == 1
    channel.basic_ack.assert_called_once_with(delivery_tag=7)


def test_exhausted_delivery_is_dead_lettered():
    channel, method, properties = create_delivery(headers={"x-retry-count": 3})
    use_case = Mock()
    use_case.execute.side_effect = RuntimeError("merchant unavailable")

    create_consumer(use_case).handle_message(
        channel,
        method,
        properties,
        create_body(),
    )

    published = channel.basic_publish.call_args.kwargs
    assert published["exchange"] == "webhook.dead-letter"
    channel.basic_ack.assert_called_once_with(delivery_tag=7)


def test_invalid_message_is_dead_lettered_without_delivery():
    channel, method, properties = create_delivery()
    use_case = Mock()

    create_consumer(use_case).handle_message(
        channel,
        method,
        properties,
        b"not-json",
    )

    use_case.execute.assert_not_called()
    exchange = channel.basic_publish.call_args.kwargs["exchange"]
    assert exchange == "webhook.dead-letter"
