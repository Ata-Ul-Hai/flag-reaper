from app.checkout import checkout, render_checkout_page

from app import flags


def setup_function(fn):
    flags.reset_overrides()


def test_checkout_defaults_to_v1():
    cart = {"items": [{"sku": "x", "price": 10.0, "qty": 2}]}
    result = checkout(cart)
    assert result["version"] == 1
    assert result["total"] == 20.0


def test_checkout_v2_when_flag_on():
    flags.set_test_override("new-checkout-flow", True)
    cart = {"items": [{"sku": "x", "price": 10.0, "qty": 2}]}
    result = checkout(cart)
    assert result["version"] == 2


def test_render_page_classic_by_default():
    assert "classic-checkout" in render_checkout_page({"items": []})


def test_render_page_v3_when_flag_on():
    flags.set_test_override("checkout-redesign", True)
    assert "v3-checkout" in render_checkout_page({"items": []})
