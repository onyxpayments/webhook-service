import logging
import signal

from app.adapters.inbound.messaging.payment_notification_consumer import (
    PaymentNotificationConsumer,
)
from app.bootstrap import get_deliver_payment_notification_use_case
from config.settings import settings


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    consumer = PaymentNotificationConsumer(
        settings=settings,
        use_case_factory=get_deliver_payment_notification_use_case,
    )
    signal.signal(signal.SIGTERM, lambda *_: consumer.stop())
    signal.signal(signal.SIGINT, lambda *_: consumer.stop())
    consumer.run_forever()


if __name__ == "__main__":
    main()
