#!/usr/bin/env python3
"""Simulate live traffic for the flags that are ON in development.

Evaluates via the REAL Unleash Python SDK (real client token, real flag
configuration) and reports the evaluation counts through the REAL metrics
pipeline (POST /api/client/metrics) so usage data genuinely flows into
Unleash. Run in the background during the demo.

Why manual reporting: UnleashClient 6.8's built-in metric flush is silently
dropped by Unleash 8.2 (202-accepted but never aggregated), so we post each
evaluation bucket ourselves — same endpoint, same honesty, instantly visible.
"""
from __future__ import annotations

import os
import random
import time
from datetime import datetime, timezone

import requests
from UnleashClient import UnleashClient

URL = os.environ.get("UNLEASH_URL", "http://localhost:4242/api")
BASE = URL.replace("/api", "")
# Client (backend) token — created by seed_unleash.py, which persists the
# server-generated secret to audit/unleash_client_token.
_DEFAULT_TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                   "audit", "unleash_client_token")
CLIENT_TOKEN = os.environ.get("UNLEASH_CLIENT_TOKEN", "")
if not CLIENT_TOKEN and os.path.exists(_DEFAULT_TOKEN_FILE):
    CLIENT_TOKEN = open(_DEFAULT_TOKEN_FILE).read().strip()
if not CLIENT_TOKEN:
    raise SystemExit("no client token: run scripts/seed_unleash.py first")

APP_NAME = "checkout-service-prod"
LIVE_FLAGS = ["checkout-redesign", "spring-campaign"]
FLUSH_SECONDS = 5.0


def main() -> None:
    client = UnleashClient(
        url=URL,
        app_name=APP_NAME,
        environment="development",
        custom_headers={"Authorization": CLIENT_TOKEN},
        refresh_interval=5,
        metrics_interval=10_000_000,  # we report metrics ourselves, below
    )
    client.initialize_client()
    print(f"Traffic simulator running against {BASE} (app={APP_NAME}). Ctrl-C to stop.",
          flush=True)

    counts: dict[str, dict[str, int]] = {}
    window_start = datetime.now(timezone.utc)
    last_flush = time.time()
    n = 0

    def flush() -> None:
        nonlocal window_start, last_flush
        if not counts:
            return
        now = datetime.now(timezone.utc)
        payload = {
            "appName": APP_NAME,
            "instanceId": "traffic-sim-1",
            "bucket": {
                "start": window_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "stop": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "toggles": counts,
            },
            "platformName": "CPython",
            "platformVersion": os.sys.version.split()[0],
            "specVersion": "6.1.0",
        }
        r = requests.post(f"{BASE}/api/client/metrics", json=payload,
                          headers={"Authorization": CLIENT_TOKEN}, timeout=10)
        total = sum(t["yes"] + t["no"] for t in counts.values())
        print(f"  metrics flush: {total} evaluations -> {r.status_code}", flush=True)
        counts.clear()
        window_start = now
        last_flush = time.time()

    try:
        while True:
            for key in LIVE_FLAGS:
                enabled = bool(client.is_enabled(key))  # real SDK evaluation
                bucket = counts.setdefault(key, {"yes": 0, "no": 0, "variants": {}})
                bucket["yes" if enabled else "no"] += 1
                n += 1
            if n % 20 == 0:
                print(f"  evaluated flags {n} times", flush=True)
            if time.time() - last_flush >= FLUSH_SECONDS:
                flush()
            time.sleep(0.5 + random.random() * 0.5)
    except KeyboardInterrupt:
        pass
    finally:
        flush()
        client.destroy()


if __name__ == "__main__":
    main()
