import requests

from app.config import settings


def _get(base_url: str, path: str, params: dict | None = None):
    response = requests.get(f"{base_url}{path}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _post(base_url: str, path: str, json_body: dict) -> dict:
    response = requests.post(f"{base_url}{path}", json=json_body, timeout=10)
    response.raise_for_status()
    return response.json()


def _get_or_none(base_url: str, path: str) -> dict | None:
    try:
        return _get(base_url, path)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def fetch_skus(category: str | None = None) -> list[dict]:
    params = {"category": category} if category else None
    return _get(settings.catalog_service_url, "/skus", params)["items"]


def fetch_sku(sku: str) -> dict | None:
    return _get_or_none(settings.catalog_service_url, f"/skus/{sku}")


def create_sku(payload: dict) -> dict:
    return _post(settings.catalog_service_url, "/skus", payload)


def fetch_stock(warehouse_code: str | None = None, sku: str | None = None) -> list[dict]:
    params = {k: v for k, v in {"warehouse_code": warehouse_code, "sku": sku}.items() if v}
    return _get(settings.inventory_service_url, "/stock", params or None)


def fetch_low_stock(warehouse_code: str | None = None) -> list[dict]:
    params = {"warehouse_code": warehouse_code} if warehouse_code else None
    return _get(settings.inventory_service_url, "/inventory/low-stock", params)


def fetch_suppliers(status: str | None = None) -> list[dict]:
    params = {"status": status} if status else None
    return _get(settings.supplier_service_url, "/suppliers", params)


def fetch_supplier(supplier_id: int) -> dict | None:
    return _get_or_none(settings.supplier_service_url, f"/suppliers/{supplier_id}")


def register_supplier(payload: dict) -> dict:
    return _post(settings.supplier_service_url, "/suppliers", payload)


def fetch_orders(status: str | None = None) -> list[dict]:
    params = {"status": status} if status else None
    return _get(settings.order_service_url, "/orders", params)


def fetch_order(order_id: int) -> dict | None:
    return _get_or_none(settings.order_service_url, f"/orders/{order_id}")


def create_order(payload: dict) -> dict:
    return _post(settings.order_service_url, "/orders", payload)
