def test_create_order_requires_authentication(anon_client):
    response = anon_client.post(
        "/orders",
        json={
            "customer_email": "customer@example.com",
            "line_items": [{"sku": "WIDGET-1", "warehouse_code": "WH1", "quantity": 1}],
        },
    )
    assert response.status_code == 401


def test_list_orders_does_not_require_authentication(anon_client):
    # Reads stay open — only mutations are gated.
    assert anon_client.get("/orders").status_code == 200
