# OnyxPay Webhook Service

RabbitMQ worker that delivers payment status notifications to merchant
endpoints.

The service consumes `payment.notification_requested` events published by the
Payment Orchestrator and sends an HTTP `POST` to the required
`notification_url` originally supplied with the transaction.

## Delivery flow

```text
Payment Orchestrator
    │ payment.notification.requested.v1
    ▼
RabbitMQ: webhook.payment-notifications.q
    │
    ▼
Webhook Service
    │ POST notification_url
    ▼
Merchant endpoint
```

## Merchant webhook contract

```json
{
  "event_id": "8fdd8d83-cab3-4bfd-96d8-49862d74eaac",
  "event_type": "payment.status_changed",
  "occurred_at": "2026-06-28T18:00:00+00:00",
  "transaction_id": "70b71d3f-4653-4514-bf42-9de25fd98f37",
  "provider_transaction_id": "mock_70b71d3f-4653-4514-bf42-9de25fd98f37",
  "status": "APPROVED",
  "message": "Mock bank payment approved asynchronously"
}
```

The internal `notification_url`, schema version, and correlation ID are not
forwarded to the merchant.

Every request includes:

```http
Content-Type: application/json
User-Agent: OnyxPay-Webhook/1.0
X-OnyxPay-Event-Id: 8fdd8d83-cab3-4bfd-96d8-49862d74eaac
Idempotency-Key: 8fdd8d83-cab3-4bfd-96d8-49862d74eaac
```

Any `2xx` response acknowledges the RabbitMQ message. Network errors, timeouts,
and non-success HTTP responses are retried. Merchant handlers should still be
idempotent because at-least-once delivery can produce duplicates.

## RabbitMQ topology

| Purpose | Exchange | Queue | Routing key |
| --- | --- | --- | --- |
| Input | `payment.events` | `webhook.payment-notifications.q` | `payment.notification.requested.v1` |
| Retry | `webhook.retry` | `webhook.payment-notifications.retry.q` | `webhook.notification.retry` |
| Dead letter | `webhook.dead-letter` | `webhook.payment-notifications.dlq` | `webhook.notification.failed` |

Input events must use event type `payment.notification_requested` and schema
version `1`. The consumer validates the full message before delivery.

Retry messages wait for `RABBITMQ_RETRY_DELAY_MS`. When
`RABBITMQ_MAX_RETRIES` is exhausted, the original message is moved to the
dead-letter queue. Invalid JSON and invalid contracts go directly there.
Messages are acknowledged only after delivery or confirmed republishing.

## Configuration

| Variable | Default |
| --- | --- |
| `RABBITMQ_HOST` | `rabbitmq` |
| `RABBITMQ_PORT` | `5672` |
| `RABBITMQ_USER` | `guest` |
| `RABBITMQ_PASSWORD` | `guest` |
| `RABBITMQ_VHOST` | `/` |
| `RABBITMQ_EXCHANGE` | `payment.events` |
| `RABBITMQ_NOTIFICATION_QUEUE` | `webhook.payment-notifications.q` |
| `RABBITMQ_NOTIFICATION_ROUTING_KEY` | `payment.notification.requested.v1` |
| `RABBITMQ_RETRY_EXCHANGE` | `webhook.retry` |
| `RABBITMQ_RETRY_QUEUE` | `webhook.payment-notifications.retry.q` |
| `RABBITMQ_RETRY_ROUTING_KEY` | `webhook.notification.retry` |
| `RABBITMQ_DEAD_LETTER_EXCHANGE` | `webhook.dead-letter` |
| `RABBITMQ_DEAD_LETTER_QUEUE` | `webhook.payment-notifications.dlq` |
| `RABBITMQ_DEAD_LETTER_ROUTING_KEY` | `webhook.notification.failed` |
| `RABBITMQ_RETRY_DELAY_MS` | `5000` |
| `RABBITMQ_MAX_RETRIES` | `3` |
| `RABBITMQ_RECONNECT_DELAY_SECONDS` | `2` |
| `WEBHOOK_TIMEOUT_SECONDS` | `5` |

## Local development

Requirements: Python 3.13 and RabbitMQ.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m app.worker
```

Quality checks:

```bash
make lint
make test
```

## Docker and Compose

```bash
docker build -t webhook-service .
docker run --rm \
  -e RABBITMQ_HOST=host.docker.internal \
  webhook-service
```

The Compose stack uses:

```text
ghcr.io/onyxpayments/webhook-service:latest
```

## Health check

The worker has no public HTTP API. Run `python -m app.worker_health` to verify
that it can connect to RabbitMQ. Docker Compose uses this command for container
health.

## Project structure

```text
.
├── app
│   ├── consumer.py        # RabbitMQ topology, ACK, retry, and DLQ logic
│   ├── delivery.py        # Merchant HTTP delivery adapter
│   ├── rabbitmq.py        # Connection parameters
│   ├── schemas.py         # Versioned notification event contract
│   ├── settings.py        # Environment configuration
│   ├── worker.py          # Worker entry point
│   └── worker_health.py   # RabbitMQ readiness command
├── tests
├── Dockerfile
├── makefile
└── requirements.txt
```

## Current limitations

- Delivery attempts are not persisted outside RabbitMQ.
- There is no per-merchant signing secret or webhook signature yet.
- Destination URL allowlisting and private-network blocking are not
  implemented.
