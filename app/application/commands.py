from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DeliverPaymentNotificationCommand:
    event_id: UUID
    occurred_at: datetime
    transaction_id: UUID
    provider_transaction_id: str
    status: str
    message: str | None
    notification_url: str
