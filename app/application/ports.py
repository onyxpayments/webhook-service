from typing import Protocol

from app.domain.models import PaymentNotification


class WebhookClient(Protocol):
    def deliver(self, notification: PaymentNotification) -> None: ...
