import fakeredis

from app.cache import SkuCache
from app.consumer import handle_pricing_update


def test_handle_pricing_update_invalidates_the_named_sku():
    cache = SkuCache(fakeredis.FakeRedis())
    cache.set("WIDGET-1", {"sku": "WIDGET-1", "unit_price": 9.99})

    handle_pricing_update(cache, {"sku": "WIDGET-1"})

    assert cache.get("WIDGET-1") is None


def test_handle_pricing_update_leaves_other_skus_alone():
    cache = SkuCache(fakeredis.FakeRedis())
    cache.set("WIDGET-1", {"sku": "WIDGET-1"})
    cache.set("GADGET-1", {"sku": "GADGET-1"})

    handle_pricing_update(cache, {"sku": "WIDGET-1"})

    assert cache.get("GADGET-1") == {"sku": "GADGET-1"}


def test_handle_pricing_update_ignores_malformed_message():
    cache = SkuCache(fakeredis.FakeRedis())
    handle_pricing_update(cache, {})  # no "sku" key — must not raise
