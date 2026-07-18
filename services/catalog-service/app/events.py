import json
from typing import Protocol


class EventPublisher(Protocol):
    def publish(self, event_type: str, payload: dict, correlation_id: str) -> None: ...


class SqsEventPublisher:
    """Publishes events to an SQS-API-compatible queue (ElasticMQ locally, AWS SQS in prod)."""

    def __init__(self, sqs_client, queue_url: str):
        self._sqs = sqs_client
        self._queue_url = queue_url

    def publish(self, event_type: str, payload: dict, correlation_id: str) -> None:
        self._sqs.send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps({"event": event_type, **payload}),
            MessageAttributes={
                "correlation_id": {"DataType": "String", "StringValue": correlation_id},
            },
        )


def make_sqs_client(endpoint_url: str):
    import boto3

    return boto3.client(
        "sqs",
        endpoint_url=endpoint_url,
        region_name="elasticmq",
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )
