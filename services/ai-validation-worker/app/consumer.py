"""Standalone SQS consumer: runs the async anomaly-detection pass on
ingestion.record_received events and publishes the verdict to
validation-result-queue.

Failures are deliberately NOT acked (the message is not deleted) — ElasticMQ
(and real SQS) redrives an unacked message to the DLQ configured in
infra/elasticmq.conf after maxReceiveCount, so a Groq outage or malformed
record surfaces as a DLQ entry to investigate rather than a silently
dropped validation.

Run with: python -m app
"""

from app.config import settings
from app.events import SqsEventPublisher, delete_message, make_sqs_client, receive_messages
from app.handler import process_message
from app.validator import GroqValidator


def run() -> None:
    sqs_client = make_sqs_client(settings.sqs_endpoint_url)
    publisher = SqsEventPublisher(sqs_client, settings.validation_result_queue_url)
    validator = GroqValidator(settings.groq_api_key, settings.groq_base_url, settings.groq_model)

    print(f"ai-validation-worker polling {settings.ai_validation_queue_url}")
    while True:
        for message in receive_messages(sqs_client, settings.ai_validation_queue_url):
            try:
                result = process_message(message["body"], validator)
            except Exception as exc:  # noqa: BLE001 — any failure must redrive to the DLQ, not vanish
                print(f"validation failed, leaving message for redrive: {exc}")
                continue
            publisher.publish("validation.completed", result, message["correlation_id"])
            delete_message(sqs_client, settings.ai_validation_queue_url, message["receipt_handle"])


if __name__ == "__main__":
    run()
