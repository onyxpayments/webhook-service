from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PaymentNotification:
    event_id: UUID
    occurred_at: datetime
    transaction_id: UUID
    provider_transaction_id: str
    status: str
    message: str | None
    notification_url: str

    def merchant_payload(self) -> dict:
        return {
            "event_id": str(self.event_id),
            "event_type": "payment.status_changed",
            "occurred_at": self.occurred_at.isoformat(),
            "transaction_id": str(self.transaction_id),
            "provider_transaction_id": self.provider_transaction_id,
            "status": self.status,
            "message": self.message,
        }
