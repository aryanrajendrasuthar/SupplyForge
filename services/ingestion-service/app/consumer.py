"""Standalone SQS consumer: applies validation.completed events (published by
ai-validation-worker) onto the matching record. Deployed as its own
process/container — see docs/architecture.md for the async validation flow.

Run with: python -m app.consumer
"""

from app import create_app
from app.config import settings
from app.events import delete_message, make_sqs_client, receive_messages
from app.repository import apply_validation_result


def run() -> None:
    app = create_app()
    sqs_client = make_sqs_client(settings.sqs_endpoint_url)

    print(f"ingestion-service consumer polling {settings.validation_result_queue_url}")
    while True:
        for message in receive_messages(sqs_client, settings.validation_result_queue_url):
            body = message["body"]
            apply_validation_result(
                app.records_collection, body["record_id"], body["is_anomalous"], body.get("reason")
            )
            delete_message(sqs_client, settings.validation_result_queue_url, message["receipt_handle"])


if __name__ == "__main__":
    run()
