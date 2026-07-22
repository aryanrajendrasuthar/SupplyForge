def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"service": "graphql-gateway", "status": "ok"}


def test_graphql_health_query(client):
    response = client.post("/graphql", json={"query": "{ health }"})
    assert response.status_code == 200
    assert response.get_json()["data"]["health"] == "ok"
