from orders import get_order, sanitize_order, order_lookup


def test_order_lookup():
    order = get_order("ord-1007")

    assert order is not None
    assert order["order_id"] == "ORD-1007"


def test_unknown_order():
    order = get_order("ORD-9999")

    assert order is None


def test_order_lookup_tool():
    order = order_lookup("ORD-1007")

    assert order is not None
    assert order["order_id"] == "ORD-1007"


def test_private_data_removed():
    order = order_lookup("ORD-1007")

    assert "email" not in order
    assert "shipping_address" not in order
    assert "internal_note" not in order
    assert "risk_score" not in order


def test_cancelled_order():
    order = order_lookup("ORD-1004")

    assert order["status"].lower() == "cancelled"
    assert order["estimated_delivery"] is None