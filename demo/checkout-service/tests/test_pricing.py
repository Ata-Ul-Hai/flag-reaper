from app import flags
from app.pricing import apply_discounts


def setup_function(fn):
    flags.reset_overrides()


def test_no_discount_by_default():
    cart = {"items": [{"sku": "x", "price": 100.0, "qty": 1}]}
    result = apply_discounts(cart)
    assert result["total"] == 100.0


def test_spring_coupon_applies_ten_percent():
    cart = {"items": [{"sku": "x", "price": 100.0, "qty": 1}], "coupons": ["SPRING10"]}
    assert apply_discounts(cart)["total"] == 90.0


def test_loyal_coupon_applies_five_percent():
    cart = {"items": [{"sku": "x", "price": 100.0, "qty": 1}], "coupons": ["LOYAL5"]}
    assert apply_discounts(cart)["total"] == 95.0
