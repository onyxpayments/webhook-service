from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = Field(default=5672, ge=1, le=65535)
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"
    rabbitmq_exchange: str = "payment.events"
    rabbitmq_notification_queue: str = "webhook.payment-notifications.q"
    rabbitmq_notification_routing_key: str = "payment.notification.requested.v1"
    webhook_retry_exchange: str = "webhook.retry"
    webhook_retry_queue: str = "webhook.payment-notifications.retry.q"
    webhook_retry_routing_key: str = "webhook.notification.retry"
    webhook_dead_letter_exchange: str = "webhook.dead-letter"
    webhook_dead_letter_queue: str = "webhook.payment-notifications.dlq"
    webhook_dead_letter_routing_key: str = "webhook.notification.failed"
    webhook_retry_delay_ms: int = Field(default=5000, ge=100)
    webhook_max_retries: int = Field(default=3, ge=0)
    webhook_reconnect_delay_seconds: float = Field(default=2, ge=0.1)
    webhook_timeout_seconds: float = Field(default=5, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
