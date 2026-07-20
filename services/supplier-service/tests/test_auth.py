def test_register_returns_201_without_password_in_response(client):
    response = client.post(
        "/auth/register", json={"email": "a@example.com", "password": "correct horse battery staple"}
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["email"] == "a@example.com"
    assert body["role"] == "analyst"  # default role
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_duplicate_email(client):
    payload = {"email": "a@example.com", "password": "correct horse battery staple"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post("/auth/register", json={"email": "a@example.com", "password": "short"})
    assert response.status_code == 400


def test_register_rejects_invalid_role(client):
    response = client.post(
        "/auth/register",
        json={"email": "a@example.com", "password": "correct horse battery staple", "role": "superadmin"},
    )
    assert response.status_code == 400


def test_login_succeeds_and_sets_session_cookie(client):
    client.post(
        "/auth/register",
        json={"email": "a@example.com", "password": "correct horse battery staple", "role": "approver"},
    )
    response = client.post(
        "/auth/login", json={"email": "a@example.com", "password": "correct horse battery staple"}
    )
    assert response.status_code == 200
    assert "sf_session" in response.headers.get("Set-Cookie", "")


def test_login_rejects_wrong_password(client):
    client.post("/auth/register", json={"email": "a@example.com", "password": "correct horse battery staple"})
    response = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong password"})
    assert response.status_code == 401


def test_login_rejects_unknown_email(client):
    response = client.post("/auth/login", json={"email": "nope@example.com", "password": "whatever password"})
    assert response.status_code == 401


def test_logout_requires_session(client):
    assert client.post("/auth/logout").status_code == 401


def test_logout_revokes_session(client):
    password = "correct horse battery staple"
    client.post("/auth/register", json={"email": "a@example.com", "password": password, "role": "approver"})
    client.post("/auth/login", json={"email": "a@example.com", "password": password})

    assert client.post("/auth/logout").status_code == 200

    # The now-revoked session cookie is still attached, but it must not work anymore.
    response = client.post("/suppliers/9999/approve")
    assert response.status_code == 401
