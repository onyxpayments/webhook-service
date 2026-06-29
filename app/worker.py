import logging
import signal

from app.consumer import PaymentNotificationConsumer
from app.delivery import WebhookDelivery
from app.settings import settings


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    consumer = PaymentNotificationConsumer(
        settings=settings,
        delivery_factory=lambda: WebhookDelivery(
            timeout_seconds=settings.webhook_timeout_seconds
        ),
    )
    signal.signal(signal.SIGTERM, lambda *_: consumer.stop())
    signal.signal(signal.SIGINT, lambda *_: consumer.stop())
    consumer.run_forever()


if __name__ == "__main__":
    main()
