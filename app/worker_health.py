import sys

import pika

from app.rabbitmq import connection_parameters
from app.settings import settings


def main() -> None:
    try:
        connection = pika.BlockingConnection(connection_parameters(settings))
        connection.close()
    except pika.exceptions.AMQPError:
        sys.exit(1)


if __name__ == "__main__":
    main()
