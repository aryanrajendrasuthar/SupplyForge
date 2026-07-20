from datetime import timedelta

import fakeredis

from supplyforge_auth import SessionStore


def make_store(ttl: timedelta = timedelta(hours=12)) -> SessionStore:
    return SessionStore(fakeredis.FakeRedis(), ttl=ttl)


def test_create_returns_high_entropy_token():
    token = make_store().create({"user_id": "user-1", "role": "approver"})
    assert len(token) >= 32


def test_resolve_returns_session_data_for_valid_token():
    store = make_store()
    token = store.create({"user_id": "user-1", "role": "approver"})
    assert store.resolve(token) == {"user_id": "user-1", "role": "approver"}


def test_resolve_returns_none_for_unknown_token():
    assert make_store().resolve("not-a-real-token") is None


def test_revoke_invalidates_token():
    store = make_store()
    token = store.create({"user_id": "user-1", "role": "approver"})
    store.revoke(token)
    assert store.resolve(token) is None


def test_revoke_all_for_user_leaves_other_users_sessions_intact():
    store = make_store()
    token_a = store.create({"user_id": "user-a", "role": "approver"})
    token_b = store.create({"user_id": "user-b", "role": "analyst"})
    store.revoke_all_for_user("user-a")
    assert store.resolve(token_a) is None
    assert store.resolve(token_b) == {"user_id": "user-b", "role": "analyst"}
