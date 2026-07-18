"""Standalone SQS consumer process: reserves stock for order.created events
(published by order-service) and publishes the result back. Deployed as its
own process/container — see docs/architecture.md for the saga flow.

Run with: python -m app.consumer
"""

from app import create_app
from app.config import settings
from app.events import SqsEventPublisher, delete_message, make_sqs_client, receive_messages
from app.saga import handle_order_created


def run() -> None:
    app = create_app()
    sqs_client = make_sqs_client(settings.sqs_endpoint_url)
    publisher = SqsEventPublisher(sqs_client, settings.order_status_queue_url)

    with app.app_context():
        db = app.session_factory()
        print(f"inventory-service consumer polling {settings.reservation_queue_url}")
        while True:
            for message in receive_messages(sqs_client, settings.reservation_queue_url):
                handle_order_created(db, publisher, message["body"], message["correlation_id"])
                delete_message(sqs_client, settings.reservation_queue_url, message["receipt_handle"])


if __name__ == "__main__":
    run()
