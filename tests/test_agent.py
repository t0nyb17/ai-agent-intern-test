from orders import get_order, sanitize_order


def test_order_exists():
    order = get_order("ORD-1007")

    assert order is not None
    assert order["order_id"] == "ORD-1007"


def test_order_id_is_case_insensitive():
    order = get_order("ord-1007")

    assert order is not None
    assert order["order_id"] == "ORD-1007"


def test_unknown_order():
    order = get_order("ORD-9999")

    assert order is None


def test_private_fields_are_removed():
    order = get_order("ORD-1007")
    safe = sanitize_order(order)

    assert "email" not in safe
    assert "shipping_address" not in safe
    assert "internal_note" not in safe
    assert "risk_score" not in safe


def test_cancelled_order_has_no_delivery_estimate():
    order = get_order("ORD-1004")
    safe = sanitize_order(order)

    assert safe["status"].lower() == "cancelled"
    assert safe["estimated_delivery"] is None