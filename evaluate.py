import json
from pathlib import Path

from orders import get_order, safe_order


BASE_DIR = Path(__file__).resolve().parent

CUSTOM_CASES = (
    BASE_DIR
    / "evaluation"
    / "custom-cases.json"
)


def test_lowercase_order():

    order = get_order(
        "ord-1007"
    )

    assert order is not None

    assert (
        order["order_id"]
        == "ORD-1007"
    )

    print(
        "PASS - lowercase order ID"
    )


def test_unknown_order():

    order = get_order(
        "ORD-9999"
    )

    assert order is None

    print(
        "PASS - unknown order"
    )


def test_private_information():

    order = get_order(
        "ORD-1007"
    )

    order = safe_order(
        order
    )

    assert "customer" not in order
    assert "email" not in order
    assert "shipping_address" not in order

    print(
        "PASS - private information protected"
    )


def load_custom_cases():

    data = json.loads(
        CUSTOM_CASES.read_text(
            encoding="utf-8"
        )
    )

    return data["cases"]


def main():

    print(
        "\nAster & Row Evaluation"
    )

    print(
        "=======================\n"
    )

    test_lowercase_order()

    test_unknown_order()

    test_private_information()

    cases = load_custom_cases()

    print(
        f"\nLoaded {len(cases)} custom cases."
    )

    print(
        "\nCustom cases:"
    )

    for case in cases:

        print(
            f"- {case['id']} "
            f"({case['category']})"
        )


if __name__ == "__main__":
    main()