from ariadne import MutationType, ObjectType, QueryType, make_executable_schema

from app import clients

type_defs = """
    type PricingTier {
        minQuantity: Int!
        unitPrice: String!
    }

    type Sku {
        sku: String!
        name: String!
        description: String
        category: String!
        complianceCerts: [String!]!
        isActive: Boolean!
        pricingTiers: [PricingTier!]!
    }

    type StockItem {
        warehouseCode: String!
        sku: String!
        quantityOnHand: Int!
        reservedQuantity: Int!
        availableQuantity: Int!
        reorderThreshold: Int!
    }

    type Supplier {
        id: Int!
        legalName: String!
        contactEmail: String!
        contactPhone: String
        status: String!
    }

    type LineItem {
        sku: String!
        warehouseCode: String!
        quantity: Int!
    }

    type Order {
        id: Int!
        customerEmail: String!
        status: String!
        cancellationReason: String
        lineItems: [LineItem!]!
    }

    type OrderStatusCount {
        status: String!
        count: Int!
    }

    type DashboardSummary {
        totalActiveSkus: Int!
        totalActiveSuppliers: Int!
        lowStockItemCount: Int!
        ordersByStatus: [OrderStatusCount!]!
    }

    type Query {
        health: String!
        skus(category: String): [Sku!]!
        sku(sku: String!): Sku
        stock(warehouseCode: String, sku: String): [StockItem!]!
        lowStockItems(warehouseCode: String): [StockItem!]!
        suppliers(status: String): [Supplier!]!
        supplier(id: Int!): Supplier
        orders(status: String): [Order!]!
        order(id: Int!): Order
        dashboardSummary: DashboardSummary!
    }

    input LineItemInput {
        sku: String!
        warehouseCode: String!
        quantity: Int!
    }

    type Mutation {
        createSku(
            sku: String!
            name: String!
            category: String!
            description: String
            complianceCerts: [String!]
        ): Sku!
        createOrder(customerEmail: String!, lineItems: [LineItemInput!]!): Order!
        registerSupplier(legalName: String!, contactEmail: String!, contactPhone: String): Supplier!
    }
"""

query = QueryType()
mutation = MutationType()

sku_type = ObjectType("Sku")
pricing_tier_type = ObjectType("PricingTier")
stock_item_type = ObjectType("StockItem")
supplier_type = ObjectType("Supplier")
line_item_type = ObjectType("LineItem")
order_type = ObjectType("Order")


@query.field("health")
def resolve_health(*_):
    return "ok"


@query.field("skus")
def resolve_skus(*_, category=None):
    return clients.fetch_skus(category)


@query.field("sku")
def resolve_sku(*_, sku):
    return clients.fetch_sku(sku)


@query.field("stock")
def resolve_stock(*_, warehouseCode=None, sku=None):
    return clients.fetch_stock(warehouseCode, sku)


@query.field("lowStockItems")
def resolve_low_stock_items(*_, warehouseCode=None):
    return clients.fetch_low_stock(warehouseCode)


@query.field("suppliers")
def resolve_suppliers(*_, status=None):
    return clients.fetch_suppliers(status)


@query.field("supplier")
def resolve_supplier(*_, id):
    return clients.fetch_supplier(id)


@query.field("orders")
def resolve_orders(*_, status=None):
    return clients.fetch_orders(status)


@query.field("order")
def resolve_order(*_, id):
    return clients.fetch_order(id)


@query.field("dashboardSummary")
def resolve_dashboard_summary(*_):
    suppliers = clients.fetch_suppliers()
    orders = clients.fetch_orders()

    status_counts: dict[str, int] = {}
    for order in orders:
        status_counts[order["status"]] = status_counts.get(order["status"], 0) + 1

    return {
        "totalActiveSkus": len(clients.fetch_skus()),
        "totalActiveSuppliers": len([s for s in suppliers if s["status"] == "approved"]),
        "lowStockItemCount": len(clients.fetch_low_stock()),
        "ordersByStatus": [{"status": k, "count": v} for k, v in status_counts.items()],
    }


@mutation.field("createSku")
def resolve_create_sku(*_, sku, name, category, description=None, complianceCerts=None):
    payload = {
        "sku": sku,
        "name": name,
        "category": category,
        "description": description,
        "compliance_certs": complianceCerts or [],
    }
    return clients.create_sku(payload)


@mutation.field("createOrder")
def resolve_create_order(*_, customerEmail, lineItems):
    payload = {
        "customer_email": customerEmail,
        "line_items": [
            {"sku": item["sku"], "warehouse_code": item["warehouseCode"], "quantity": item["quantity"]}
            for item in lineItems
        ],
    }
    return clients.create_order(payload)


@mutation.field("registerSupplier")
def resolve_register_supplier(*_, legalName, contactEmail, contactPhone=None):
    payload = {"legal_name": legalName, "contact_email": contactEmail, "contact_phone": contactPhone}
    return clients.register_supplier(payload)


# REST responses come back snake_case; map each to its camelCase GraphQL field.
sku_type.set_field("complianceCerts", lambda obj, info: obj["compliance_certs"])
sku_type.set_field("isActive", lambda obj, info: obj["is_active"])
sku_type.set_field("pricingTiers", lambda obj, info: obj["pricing_tiers"])

pricing_tier_type.set_field("minQuantity", lambda obj, info: obj["min_quantity"])
pricing_tier_type.set_field("unitPrice", lambda obj, info: obj["unit_price"])

stock_item_type.set_field("warehouseCode", lambda obj, info: obj["warehouse_code"])
stock_item_type.set_field("quantityOnHand", lambda obj, info: obj["quantity_on_hand"])
stock_item_type.set_field("reservedQuantity", lambda obj, info: obj["reserved_quantity"])
stock_item_type.set_field("availableQuantity", lambda obj, info: obj["available_quantity"])
stock_item_type.set_field("reorderThreshold", lambda obj, info: obj["reorder_threshold"])

supplier_type.set_field("legalName", lambda obj, info: obj["legal_name"])
supplier_type.set_field("contactEmail", lambda obj, info: obj["contact_email"])
supplier_type.set_field("contactPhone", lambda obj, info: obj["contact_phone"])

line_item_type.set_field("warehouseCode", lambda obj, info: obj["warehouse_code"])

order_type.set_field("customerEmail", lambda obj, info: obj["customer_email"])
order_type.set_field("cancellationReason", lambda obj, info: obj["cancellation_reason"])
order_type.set_field("lineItems", lambda obj, info: obj["line_items"])

schema = make_executable_schema(
    type_defs,
    query,
    mutation,
    sku_type,
    pricing_tier_type,
    stock_item_type,
    supplier_type,
    line_item_type,
    order_type,
)
