from app.validator import Validator


def process_message(event: dict, validator: Validator) -> dict:
    """Runs the anomaly-detection pass for one ingested record.

    Returns the payload to publish on validation-result-queue. Any exception
    here (e.g. the Groq call failing) is intentionally left to propagate —
    the caller must not delete the SQS message on failure, so it redrives to
    the DLQ after maxReceiveCount (see infra/elasticmq.conf) instead of the
    record silently never getting validated.
    """
    verdict = validator.validate(event["payload"])
    return {
        "record_id": event["record_id"],
        "is_anomalous": verdict["is_anomalous"],
        "reason": verdict["reason"],
    }
