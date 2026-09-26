"""Pricing and discounts. `spring-campaign` gates the seasonal discount."""
from __future__ import annotations

from .flags import is_enabled


def apply_discounts(cart: dict) -> dict:
    total = sum(item["price"] * item["qty"] for item in cart["items"])

    if is_enabled("spring-campaign"):
        cart.setdefault("coupons", []).append("SPRING10")

    for coupon in cart.get("coupons", []):
        if coupon == "SPRING10":
            total *= 0.90
        elif coupon == "LOYAL5":
            total *= 0.95

    return {"total": round(total, 2), "coupons": cart.get("coupons", [])}
