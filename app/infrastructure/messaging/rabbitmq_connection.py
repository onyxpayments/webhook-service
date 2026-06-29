import pika

from config.settings import Settings


def connection_parameters(settings: Settings) -> pika.ConnectionParameters:
    return pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        virtual_host=settings.rabbitmq_vhost,
        credentials=pika.PlainCredentials(
            settings.rabbitmq_user,
            settings.rabbitmq_password,
        ),
        heartbeat=30,
        blocked_connection_timeout=5,
        socket_timeout=3,
        connection_attempts=3,
        retry_delay=1,
    )
