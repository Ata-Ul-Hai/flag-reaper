"""checkout-service — run with UNLEASH_URL set to evaluate live flags."""
import json
import os


def main() -> None:
    from .checkout import checkout, render_checkout_page
    from .pricing import apply_discounts
    from .recommendations import checkout_summary

    cart = {"items": [{"sku": "t-shirt", "price": 25.0, "qty": 2}], "guest": False}
    print(json.dumps({
        "checkout": checkout(cart),
        "page": render_checkout_page(cart),
        "pricing": apply_discounts(dict(cart, coupons=[])),
        "summary": checkout_summary(cart),
    }, indent=2))


if __name__ == "__main__":
    if not os.environ.get("UNLEASH_URL"):
        print("Set UNLEASH_URL (e.g. http://localhost:4242) for live mode.")
    main()
