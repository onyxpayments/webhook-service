import logging
import time
from collections.abc import Callable

import pika
from pydantic import ValidationError

from app.delivery import WebhookDelivery
from app.rabbitmq import connection_parameters
from app.schemas import PaymentNotificationMessage
from app.settings import Settings

logger = logging.getLogger(__name__)


class PaymentNotificationConsumer:
    def __init__(
        self,
        settings: Settings,
        delivery_factory: Callable[[], WebhookDelivery],
    ):
        self.settings = settings
        self.delivery_factory = delivery_factory
        self.connection = None
        self.channel = None
        self.stopping = False

    def run_forever(self) -> None:
        while not self.stopping:
            try:
                self.connection = pika.BlockingConnection(
                    connection_parameters(self.settings)
                )
                self.channel = self.connection.channel()
                self._declare_topology(self.channel)
                self.channel.confirm_delivery()
                self.channel.basic_qos(prefetch_count=1)
                self.channel.basic_consume(
                    queue=self.settings.rabbitmq_notification_queue,
                    on_message_callback=self.handle_message,
                    auto_ack=False,
                )
                logger.info(
                    "Consuming payment notifications from %s",
                    self.settings.rabbitmq_notification_queue,
                )
                self.channel.start_consuming()
            except pika.exceptions.AMQPError:
                logger.exception("RabbitMQ consumer connection failed")
            finally:
                self._close_connection()

            if not self.stopping:
                time.sleep(self.settings.rabbitmq_reconnect_delay_seconds)

    def stop(self) -> None:
        self.stopping = True
        if self.connection and self.connection.is_open and self.channel:
            callback = self.channel.stop_consuming
            self.connection.add_callback_threadsafe(callback)

    def handle_message(self, channel, method, properties, body: bytes) -> None:
        try:
            notification = PaymentNotificationMessage.model_validate_json(body)
        except ValidationError as error:
            logger.warning("Invalid notification message: %s", error)
            self._dead_letter(channel, method.delivery_tag, properties, body)
            return

        try:
            self.delivery_factory().deliver(notification)
        except Exception:
            logger.exception(
                "Webhook delivery failed for event %s",
                notification.event_id,
            )
            self._retry_or_dead_letter(
                channel,
                method.delivery_tag,
                properties,
                body,
            )
            return

        channel.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("Webhook event %s delivered", notification.event_id)

    def _declare_topology(self, channel) -> None:
        settings = self.settings
        channel.exchange_declare(
            exchange=settings.rabbitmq_exchange,
            exchange_type="topic",
            durable=True,
        )
        channel.queue_declare(
            queue=settings.rabbitmq_notification_queue,
            durable=True,
        )
        channel.queue_bind(
            exchange=settings.rabbitmq_exchange,
            queue=settings.rabbitmq_notification_queue,
            routing_key=settings.rabbitmq_notification_routing_key,
        )

        channel.exchange_declare(
            exchange=settings.rabbitmq_retry_exchange,
            exchange_type="direct",
            durable=True,
        )
        channel.queue_declare(
            queue=settings.rabbitmq_retry_queue,
            durable=True,
            arguments={
                "x-message-ttl": settings.rabbitmq_retry_delay_ms,
                "x-dead-letter-exchange": settings.rabbitmq_exchange,
                "x-dead-letter-routing-key": (
                    settings.rabbitmq_notification_routing_key
                ),
            },
        )
        channel.queue_bind(
            exchange=settings.rabbitmq_retry_exchange,
            queue=settings.rabbitmq_retry_queue,
            routing_key=settings.rabbitmq_retry_routing_key,
        )

        channel.exchange_declare(
            exchange=settings.rabbitmq_dead_letter_exchange,
            exchange_type="direct",
            durable=True,
        )
        channel.queue_declare(
            queue=settings.rabbitmq_dead_letter_queue,
            durable=True,
        )
        channel.queue_bind(
            exchange=settings.rabbitmq_dead_letter_exchange,
            queue=settings.rabbitmq_dead_letter_queue,
            routing_key=settings.rabbitmq_dead_letter_routing_key,
        )

    def _retry_or_dead_letter(
        self,
        channel,
        delivery_tag: int,
        properties,
        body: bytes,
    ) -> None:
        headers = dict(properties.headers or {})
        retry_count = int(headers.get("x-retry-count", 0))
        if retry_count >= self.settings.rabbitmq_max_retries:
            self._dead_letter(channel, delivery_tag, properties, body)
            return

        headers["x-retry-count"] = retry_count + 1
        if self._publish(
            channel,
            self.settings.rabbitmq_retry_exchange,
            self.settings.rabbitmq_retry_routing_key,
            properties,
            headers,
            body,
        ):
            channel.basic_ack(delivery_tag=delivery_tag)
        else:
            channel.basic_nack(delivery_tag=delivery_tag, requeue=True)

    def _dead_letter(
        self,
        channel,
        delivery_tag: int,
        properties,
        body: bytes,
    ) -> None:
        headers = dict(properties.headers or {})
        if self._publish(
            channel,
            self.settings.rabbitmq_dead_letter_exchange,
            self.settings.rabbitmq_dead_letter_routing_key,
            properties,
            headers,
            body,
        ):
            channel.basic_ack(delivery_tag=delivery_tag)
        else:
            channel.basic_nack(delivery_tag=delivery_tag, requeue=True)

    @staticmethod
    def _publish(
        channel,
        exchange: str,
        routing_key: str,
        properties,
        headers: dict,
        body: bytes,
    ) -> bool:
        try:
            return (
                channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    body=body,
                    properties=pika.BasicProperties(
                        content_type=(
                            properties.content_type or "application/json"
                        ),
                        delivery_mode=2,
                        message_id=properties.message_id,
                        correlation_id=properties.correlation_id,
                        type=properties.type,
                        headers=headers,
                    ),
                    mandatory=True,
                )
                is not False
            )
        except pika.exceptions.AMQPError:
            logger.exception("Could not republish webhook message")
            return False

    def _close_connection(self) -> None:
        if self.connection and self.connection.is_open:
            self.connection.close()
