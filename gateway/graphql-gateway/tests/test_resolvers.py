from app import clients


def graphql_query(client, query: str, variables: dict | None = None):
    response = client.post("/graphql", json={"query": query, "variables": variables or {}})
    return response.get_json()


def test_skus_query_maps_snake_case_fields_to_camel_case(client, monkeypatch):
    monkeypatch.setattr(
        clients,
        "fetch_skus",
        lambda category=None: [
            {
                "sku": "WIDGET-1",
                "name": "Widget",
                "description": None,
                "category": "widgets",
                "compliance_certs": ["RoHS"],
                "is_active": True,
                "pricing_tiers": [{"min_quantity": 1, "unit_price": "9.99"}],
            }
        ],
    )

    result = graphql_query(
        client,
        "{ skus { sku name complianceCerts isActive pricingTiers { minQuantity unitPrice } } }",
    )

    assert result["data"]["skus"] == [
        {
            "sku": "WIDGET-1",
            "name": "Widget",
            "complianceCerts": ["RoHS"],
            "isActive": True,
            "pricingTiers": [{"minQuantity": 1, "unitPrice": "9.99"}],
        }
    ]


def test_sku_query_passes_through_argument(client, monkeypatch):
    captured = {}

    def fake_fetch_sku(sku):
        captured["sku"] = sku
        return None

    monkeypatch.setattr(clients, "fetch_sku", fake_fetch_sku)

    result = graphql_query(client, '{ sku(sku: "WIDGET-1") { name } }')

    assert captured["sku"] == "WIDGET-1"
    assert result["data"]["sku"] is None


def test_stock_query_maps_fields(client, monkeypatch):
    monkeypatch.setattr(
        clients,
        "fetch_stock",
        lambda warehouse_code=None, sku=None: [
            {
                "warehouse_code": "WH1",
                "sku": "WIDGET-1",
                "quantity_on_hand": 10,
                "reserved_quantity": 2,
                "available_quantity": 8,
                "reorder_threshold": 3,
            }
        ],
    )

    result = graphql_query(client, "{ stock { warehouseCode availableQuantity reorderThreshold } }")

    assert result["data"]["stock"] == [{"warehouseCode": "WH1", "availableQuantity": 8, "reorderThreshold": 3}]


def test_order_query_maps_line_items(client, monkeypatch):
    monkeypatch.setattr(
        clients,
        "fetch_order",
        lambda order_id: {
            "id": order_id,
            "customer_email": "c@example.com",
            "status": "confirmed",
            "cancellation_reason": None,
            "line_items": [{"sku": "WIDGET-1", "warehouse_code": "WH1", "quantity": 2}],
        },
    )

    result = graphql_query(
        client, "{ order(id: 1) { id status lineItems { sku warehouseCode quantity } } }"
    )

    assert result["data"]["order"] == {
        "id": 1,
        "status": "confirmed",
        "lineItems": [{"sku": "WIDGET-1", "warehouseCode": "WH1", "quantity": 2}],
    }


def test_dashboard_summary_aggregates_across_services(client, monkeypatch):
    monkeypatch.setattr(clients, "fetch_skus", lambda category=None: [{"sku": "A"}, {"sku": "B"}])
    monkeypatch.setattr(
        clients,
        "fetch_suppliers",
        lambda status=None: [{"status": "approved"}, {"status": "approved"}, {"status": "registered"}],
    )
    monkeypatch.setattr(clients, "fetch_low_stock", lambda warehouse_code=None: [{"sku": "LOW-1"}])
    monkeypatch.setattr(
        clients,
        "fetch_orders",
        lambda status=None: [{"status": "confirmed"}, {"status": "confirmed"}, {"status": "cancelled"}],
    )

    result = graphql_query(
        client,
        "{ dashboardSummary { totalActiveSkus totalActiveSuppliers lowStockItemCount "
        "ordersByStatus { status count } } }",
    )

    summary = result["data"]["dashboardSummary"]
    assert summary["totalActiveSkus"] == 2
    assert summary["totalActiveSuppliers"] == 2
    assert summary["lowStockItemCount"] == 1
    assert sorted(summary["ordersByStatus"], key=lambda x: x["status"]) == [
        {"status": "cancelled", "count": 1},
        {"status": "confirmed", "count": 2},
    ]


def test_create_sku_mutation_translates_payload(client, monkeypatch):
    captured = {}

    def fake_create_sku(payload):
        captured["payload"] = payload
        return {
            "sku": payload["sku"],
            "name": payload["name"],
            "description": payload["description"],
            "category": payload["category"],
            "compliance_certs": payload["compliance_certs"],
            "is_active": True,
            "pricing_tiers": [],
        }

    monkeypatch.setattr(clients, "create_sku", fake_create_sku)

    result = graphql_query(
        client,
        'mutation { createSku(sku: "WIDGET-1", name: "Widget", category: "widgets", '
        'complianceCerts: ["RoHS"]) { sku complianceCerts } }',
    )

    assert captured["payload"]["compliance_certs"] == ["RoHS"]
    assert result["data"]["createSku"] == {"sku": "WIDGET-1", "complianceCerts": ["RoHS"]}


def test_create_order_mutation_translates_line_items(client, monkeypatch):
    captured = {}

    def fake_create_order(payload):
        captured["payload"] = payload
        return {
            "id": 1,
            "customer_email": payload["customer_email"],
            "status": "pending",
            "cancellation_reason": None,
            "line_items": payload["line_items"],
        }

    monkeypatch.setattr(clients, "create_order", fake_create_order)

    result = graphql_query(
        client,
        "mutation { createOrder(customerEmail: \"c@example.com\", "
        'lineItems: [{ sku: "WIDGET-1", warehouseCode: "WH1", quantity: 2 }]) '
        "{ id status lineItems { sku warehouseCode quantity } } }",
    )

    assert captured["payload"]["line_items"] == [{"sku": "WIDGET-1", "warehouse_code": "WH1", "quantity": 2}]
    assert result["data"]["createOrder"]["lineItems"] == [
        {"sku": "WIDGET-1", "warehouseCode": "WH1", "quantity": 2}
    ]


def test_ship_order_mutation(client, monkeypatch):
    captured = {}

    def fake_ship_order(order_id):
        captured["order_id"] = order_id
        return {"id": order_id, "customer_email": "c@example.com", "status": "shipped", "cancellation_reason": None, "line_items": []}

    monkeypatch.setattr(clients, "ship_order", fake_ship_order)

    result = graphql_query(client, "mutation { shipOrder(id: 1) { id status } }")

    assert captured["order_id"] == 1
    assert result["data"]["shipOrder"]["status"] == "shipped"


def test_deliver_order_mutation(client, monkeypatch):
    captured = {}

    def fake_deliver_order(order_id):
        captured["order_id"] = order_id
        return {"id": order_id, "customer_email": "c@example.com", "status": "delivered", "cancellation_reason": None, "line_items": []}

    monkeypatch.setattr(clients, "deliver_order", fake_deliver_order)

    result = graphql_query(client, "mutation { deliverOrder(id: 1) { id status } }")

    assert captured["order_id"] == 1
    assert result["data"]["deliverOrder"]["status"] == "delivered"
