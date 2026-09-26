"""Checkout flow: v1/v2 gated by a feature flag, plus the page renderer."""
from __future__ import annotations

from .flags import is_enabled


def _checkout_v1(cart: dict) -> dict:
    total = sum(item["price"] * item["qty"] for item in cart["items"])
    return {"version": 1, "total": round(total, 2), "status": "ok"}


def _checkout_v2(cart: dict) -> dict:
    total = sum(item["price"] * item["qty"] for item in cart["items"])
    discount = 0.05 if len(cart["items"]) >= 3 else 0.0
    return {
        "version": 2,
        "total": round(total * (1 - discount), 2),
        "status": "ok",
        "express_eligible": total > 100,
    }


def checkout(cart: dict) -> dict:
    if is_enabled("new-checkout-flow"):
        return _checkout_v2(cart)
    else:
        return _checkout_v1(cart)


def _render_classic(cart: dict) -> str:
    return f"classic-checkout:{len(cart['items'])} items"


def _render_v3(cart: dict) -> str:
    return f"v3-checkout:{len(cart['items'])} items"


def render_checkout_page(cart: dict) -> str:
    if is_enabled("checkout-redesign"):
        return _render_v3(cart)
    return _render_classic(cart)
