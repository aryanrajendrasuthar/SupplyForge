import fakeredis
import pytest
from flask import Flask, g

from supplyforge_auth import SessionStore, require_session
from supplyforge_auth.cookies import SESSION_COOKIE_NAME


@pytest.fixture
def session_store():
    return SessionStore(fakeredis.FakeRedis())


@pytest.fixture
def app(session_store):
    app = Flask(__name__)
    app.session_store = session_store

    @app.get("/open")
    def open_route():
        return {"ok": True}

    @app.get("/any-session")
    @require_session()
    def any_session_route():
        return {"user_id": g.current_user["user_id"]}

    @app.get("/approver-only")
    @require_session(role="approver")
    def approver_only_route():
        return {"user_id": g.current_user["user_id"]}

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_missing_cookie_returns_401(client):
    response = client.get("/any-session")
    assert response.status_code == 401


def test_valid_session_allows_access(client, session_store):
    token = session_store.create({"user_id": "user-1", "role": "analyst"})
    client.set_cookie(SESSION_COOKIE_NAME, token)
    response = client.get("/any-session")
    assert response.status_code == 200
    assert response.get_json() == {"user_id": "user-1"}


def test_wrong_role_returns_403(client, session_store):
    token = session_store.create({"user_id": "user-1", "role": "analyst"})
    client.set_cookie(SESSION_COOKIE_NAME, token)
    response = client.get("/approver-only")
    assert response.status_code == 403


def test_matching_role_allows_access(client, session_store):
    token = session_store.create({"user_id": "user-2", "role": "approver"})
    client.set_cookie(SESSION_COOKIE_NAME, token)
    response = client.get("/approver-only")
    assert response.status_code == 200


def test_admin_role_satisfies_any_role_check(client, session_store):
    token = session_store.create({"user_id": "user-3", "role": "admin"})
    client.set_cookie(SESSION_COOKIE_NAME, token)
    response = client.get("/approver-only")
    assert response.status_code == 200


def test_revoked_session_returns_401(client, session_store):
    token = session_store.create({"user_id": "user-1", "role": "approver"})
    session_store.revoke(token)
    client.set_cookie(SESSION_COOKIE_NAME, token)
    response = client.get("/any-session")
    assert response.status_code == 401
