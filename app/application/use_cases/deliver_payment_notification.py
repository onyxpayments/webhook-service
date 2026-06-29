from app.application.commands import DeliverPaymentNotificationCommand
from app.application.ports import WebhookClient
from app.domain.models import PaymentNotification


class DeliverPaymentNotificationUseCase:
    def __init__(self, webhook_client: WebhookClient):
        self.webhook_client = webhook_client

    def execute(self, command: DeliverPaymentNotificationCommand) -> None:
        notification = PaymentNotification(
            event_id=command.event_id,
            occurred_at=command.occurred_at,
            transaction_id=command.transaction_id,
            provider_transaction_id=command.provider_transaction_id,
            status=command.status,
            message=command.message,
            notification_url=command.notification_url,
        )
        self.webhook_client.deliver(notification)
