from app import flags
from app.recommendations import checkout_summary, recommend


def setup_function(fn):
    flags.reset_overrides()


def test_recommend_defaults_to_popular():
    cart = {"items": [{"sku": "a", "price": 1.0, "qty": 1}]}
    assert recommend(cart)[0].startswith("pop:")


def test_summary_guest_gets_popular():
    cart = {"items": [{"sku": "a", "price": 1.0, "qty": 1}], "guest": True}
    summary = checkout_summary(cart)
    assert summary["recommendations"][0].startswith("pop:")


def test_summary_signed_in_v2_ml():
    flags.set_test_override("recommendation-v2", True)
    cart = {"items": [{"sku": "a", "price": 1.0, "qty": 1}], "guest": False}
    summary = checkout_summary(cart)
    assert summary["recommendations"][0].startswith("ml:")
