import sys

import pika

from app.infrastructure.messaging.rabbitmq_connection import (
    connection_parameters,
)
from config.settings import settings


def main() -> None:
    try:
        connection = pika.BlockingConnection(connection_parameters(settings))
        connection.close()
    except pika.exceptions.AMQPError:
        sys.exit(1)


if __name__ == "__main__":
    main()
