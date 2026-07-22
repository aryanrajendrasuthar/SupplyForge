import fakeredis

from app.cache import SkuCache


def make_cache() -> SkuCache:
    return SkuCache(fakeredis.FakeRedis())


def test_get_returns_none_for_unknown_sku():
    assert make_cache().get("WIDGET-1") is None


def test_set_then_get_round_trips():
    cache = make_cache()
    cache.set("WIDGET-1", {"sku": "WIDGET-1", "name": "Widget"})
    assert cache.get("WIDGET-1") == {"sku": "WIDGET-1", "name": "Widget"}


def test_invalidate_removes_the_entry():
    cache = make_cache()
    cache.set("WIDGET-1", {"sku": "WIDGET-1"})
    cache.invalidate("WIDGET-1")
    assert cache.get("WIDGET-1") is None


def test_invalidate_unknown_sku_is_a_no_op():
    cache = make_cache()
    cache.invalidate("NOPE")  # must not raise
    assert cache.get("NOPE") is None


def test_entries_are_isolated_per_sku():
    cache = make_cache()
    cache.set("WIDGET-1", {"sku": "WIDGET-1"})
    cache.set("GADGET-1", {"sku": "GADGET-1"})
    cache.invalidate("WIDGET-1")
    assert cache.get("WIDGET-1") is None
    assert cache.get("GADGET-1") == {"sku": "GADGET-1"}
