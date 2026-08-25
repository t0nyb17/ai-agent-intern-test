import json
from pathlib import Path


ORDERS_FILE = Path(__file__).resolve().parent / "data" / "orders.json"


def get_order(order_id):
    data = json.loads(
        ORDERS_FILE.read_text(encoding="utf-8")
    )

    order_id = order_id.strip().upper()

    for order in data["orders"]:
        if order["order_id"].upper() == order_id:
            return order

    return None


def sanitize_order(order):
    if not order:
        return None

    result = {
        "order_id": order["order_id"],
        "status": order["status"],
        "shipped_at": order.get("shipped_at"),
        "delivered_at": order.get("delivered_at"),
        "carrier": order.get("carrier"),
        "tracking_number": order.get("tracking_number"),
        "estimated_delivery": order.get("estimated_delivery"),
    }

    if order["status"].lower() in ["cancelled", "returned"]:
        result["shipped_at"] = None
        result["delivered_at"] = None
        result["carrier"] = None
        result["tracking_number"] = None
        result["estimated_delivery"] = None

    return result


def order_lookup(order_id):
    return sanitize_order(get_order(order_id))