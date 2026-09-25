#!/usr/bin/env python3
"""Simulate live traffic for the flags that are ON in development.

Uses the REAL Unleash Python SDK so evaluation metrics genuinely flow through
Unleash's metrics pipeline (POST /api/client/metrics) — the reaper then reads
that usage from the Admin API. Run in the background during the demo.
"""
from __future__ import annotations

import os
import random
import time

from UnleashClient import UnleashClient

URL = os.environ.get("UNLEASH_URL", "http://localhost:4242/api")
# Client (backend) token — created by seed_unleash.py, which persists the
# server-generated secret to audit/unleash_client_token.
_DEFAULT_TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "audit", "unleash_client_token")
CLIENT_TOKEN = os.environ.get("UNLEASH_CLIENT_TOKEN", "")
if not CLIENT_TOKEN and os.path.exists(_DEFAULT_TOKEN_FILE):
    CLIENT_TOKEN = open(_DEFAULT_TOKEN_FILE).read().strip()
if not CLIENT_TOKEN:
    raise SystemExit("no client token: run scripts/seed_unleash.py first")
LIVE_FLAGS = ["checkout-redesign", "spring-campaign"]


def main() -> None:
    client = UnleashClient(
        url=URL,
        app_name="checkout-service-prod",
        environment="development",
        custom_headers={"Authorization": CLIENT_TOKEN},
        metrics_interval=5000,   # flush real metrics every 5s
        refresh_interval=5,
    )
    client.initialize_client()
    print(f"Traffic simulator running against {URL} (app=checkout-service-prod). Ctrl-C to stop.", flush=True)
    n = 0
    try:
        while True:
            for key in LIVE_FLAGS:
                client.is_enabled(key)  # each call feeds the metrics pipeline
            n += 1
            if n % 20 == 0:
                print(f"  evaluated flags {n * len(LIVE_FLAGS)} times", flush=True)
            time.sleep(0.5 + random.random() * 0.5)
    except KeyboardInterrupt:
        pass
    finally:
        client.destroy()


if __name__ == "__main__":
    main()
