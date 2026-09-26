"""Flag checks for checkout-service.

Live mode uses the real Unleash SDK. Tests/offline use static values.
"""
from __future__ import annotations

import os

_static_overrides: dict[str, bool] = {}
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    url = os.environ.get("UNLEASH_URL")
    if url:
        from UnleashClient import UnleashClient

        _client = UnleashClient(url, "checkout-service")
        _client.initialize()
    else:
        _client = "static"
    return _client


def is_enabled(flag_key: str, default: bool = False) -> bool:
    """Evaluate a feature flag. The single choke-point for all flag checks."""
    client = _get_client()
    if client == "static":
        return _static_overrides.get(flag_key, default)
    return client.is_enabled(flag_key, fallback_function=lambda *a, **k: default)


def experiment_flag(name: str) -> bool:
    """Experiment flags are constructed dynamically from experiment names."""
    return is_enabled(f"exp_{name}")


def set_test_override(flag_key: str, value: bool) -> None:
    _static_overrides[flag_key] = value


def reset_overrides() -> None:
    _static_overrides.clear()
