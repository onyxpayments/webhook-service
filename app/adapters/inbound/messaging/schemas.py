from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.application.commands import DeliverPaymentNotificationCommand


class PaymentNotificationMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: Literal["payment.notification_requested"]
    schema_version: Literal[1]
    occurred_at: datetime
    correlation_id: UUID
    transaction_id: UUID
    provider_transaction_id: str = Field(min_length=1)
    status: Literal["APPROVED", "DECLINED", "ERROR", "EXPIRED", "PENDING"]
    message: str | None = None
    notification_url: HttpUrl

    @model_validator(mode="after")
    def correlation_matches_transaction(self) -> "PaymentNotificationMessage":
        if self.correlation_id != self.transaction_id:
            raise ValueError("correlation_id must match transaction_id")
        return self

    def to_command(self) -> DeliverPaymentNotificationCommand:
        return DeliverPaymentNotificationCommand(
            event_id=self.event_id,
            occurred_at=self.occurred_at,
            transaction_id=self.transaction_id,
            provider_transaction_id=self.provider_transaction_id,
            status=self.status,
            message=self.message,
            notification_url=str(self.notification_url),
        )
