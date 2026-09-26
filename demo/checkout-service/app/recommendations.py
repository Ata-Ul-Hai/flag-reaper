"""Recommendations. `recommendation-v2` is wired into multiple call sites in
non-trivial ways (expressions, fallbacks) — the kind of flag that is easy to
get wrong when removing."""
from __future__ import annotations

from .flags import is_enabled


def _ml_recommend(cart: dict, limit: int = 5) -> list[str]:
    return [f"ml:{item['sku']}" for item in cart["items"]][:limit]


def _popular_items(limit: int = 5) -> list[str]:
    return ["pop:sku-a", "pop:sku-b", "pop:sku-c"][:limit]


def recommend(cart: dict) -> list[str]:
    if is_enabled("recommendation-v2"):
        return _ml_recommend(cart)
    return _popular_items()


def checkout_summary(cart: dict) -> dict:
    # Recommendation embedded in a bigger expression, with a second condition.
    if is_enabled("recommendation-v2") and not cart.get("guest"):
        recs = _ml_recommend(cart, limit=3)
    elif cart.get("guest"):
        recs = _popular_items(limit=3)
    else:
        recs = recommend(cart)
    return {"items": cart["items"], "recommendations": recs}
