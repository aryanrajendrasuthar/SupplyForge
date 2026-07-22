"""Standalone SQS consumer: invalidates the gateway's SKU cache the moment
catalog-service publishes pricing.updated, instead of leaving stale prices
to expire off a bare TTL. Deployed as its own process/container — see
docs/architecture.md for why.

Run with: python -m app.consumer
"""

import redis

from app.cache import SkuCache
from app.config import settings
from app.events import delete_message, make_sqs_client, receive_messages


def handle_pricing_update(cache: SkuCache, body: dict) -> None:
    sku = body.get("sku")
    if sku:
        cache.invalidate(sku)


def run() -> None:
    sqs_client = make_sqs_client(settings.sqs_endpoint_url)
    cache = SkuCache(redis.Redis.from_url(settings.redis_url))

    print(f"graphql-gateway consumer polling {settings.pricing_queue_url}")
    while True:
        for message in receive_messages(sqs_client, settings.pricing_queue_url):
            handle_pricing_update(cache, message["body"])
            delete_message(sqs_client, settings.pricing_queue_url, message["receipt_handle"])


if __name__ == "__main__":
    run()
