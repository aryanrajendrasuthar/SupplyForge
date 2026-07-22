import json


def make_sqs_client(endpoint_url: str):
    import boto3

    return boto3.client(
        "sqs",
        endpoint_url=endpoint_url,
        region_name="elasticmq",
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )


def receive_messages(sqs_client, queue_url: str, max_messages: int = 10, wait_time_seconds: int = 10) -> list[dict]:
    """Long-polls the queue; returns parsed bodies alongside their receipt handles."""
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=wait_time_seconds,
        MessageAttributeNames=["All"],
    )
    messages = []
    for raw in response.get("Messages", []):
        body = json.loads(raw["Body"])
        messages.append({"body": body, "receipt_handle": raw["ReceiptHandle"]})
    return messages


def delete_message(sqs_client, queue_url: str, receipt_handle: str) -> None:
    sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
