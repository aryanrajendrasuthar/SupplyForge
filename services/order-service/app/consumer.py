"""Standalone SQS consumer process: applies inventory.reserved /
inventory.reservation_failed events (published by inventory-service) to
their orders. Deployed as its own process/container — see
docs/architecture.md for why services don't share a request/response path
for the saga.

Run with: python -m app.consumer
"""

from app import create_app
from app.config import settings
from app.events import delete_message, make_sqs_client, receive_messages
from app.saga import handle_reservation_result


def run() -> None:
    app = create_app()
    sqs_client = make_sqs_client(settings.sqs_endpoint_url)

    with app.app_context():
        db = app.session_factory()
        print(f"order-service consumer polling {settings.order_status_queue_url}")
        while True:
            for message in receive_messages(sqs_client, settings.order_status_queue_url):
                handle_reservation_result(db, message["body"])
                delete_message(sqs_client, settings.order_status_queue_url, message["receipt_handle"])


if __name__ == "__main__":
    run()
