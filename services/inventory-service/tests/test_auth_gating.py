def test_create_warehouse_requires_authentication(anon_client):
    response = anon_client.post("/warehouses", json={"code": "WH1", "name": "Main Warehouse"})
    assert response.status_code == 401


def test_create_stock_item_requires_authentication(anon_client):
    response = anon_client.post(
        "/stock", json={"warehouse_code": "WH1", "sku": "WIDGET-1", "quantity_on_hand": 10}
    )
    assert response.status_code == 401


def test_get_stock_does_not_require_authentication(anon_client):
    # Reads stay open — only mutations are gated.
    assert anon_client.get("/stock").status_code == 200
