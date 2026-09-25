#!/usr/bin/env python3
"""Seed the local Unleash instance with the exact 8-flag demo matrix.

Idempotent: deletes + recreates the demo flags. Uses the real Admin API.
"""
from __future__ import annotations

import pathlib
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

URL = "http://localhost:4242"
TOKEN = "*:*.b8f8c6a1d2e34f5a9c7b0d8e1f2a3b4c5d6e7f8a9b0c1d2e"
H = {"Authorization": TOKEN, "Content-Type": "application/json"}
ADMIN = URL + "/api/admin"

# key, type, enabled-in-development (i.e. gets live traffic), expected verdict
FLAGS = [
    ("legacy-coupon-banner", "release",  False, "REMOVABLE (flag-only delete)"),
    ("darkmode-toggle",      "release",  False, "REMOVABLE (tests + flag)"),
    ("new-checkout-flow",    "release",  False, "REMOVABLE (code + flag)"),
    ("recommendation-v2",    "experiment", False, "STILL_LIVE (rule 6: non-trivial refs)"),
    ("checkout-redesign",    "release",  True,  "STILL_LIVE (traffic)"),
    ("spring-campaign",      "kill-switch", True,  "STILL_LIVE (traffic)"),
    ("exp_checkout",         "experiment", False, "UNKNOWN (dynamic f-string)"),
    ("beta-search-ranking",  "experiment", False, "UNKNOWN (config-map lookup)"),
]


def wait_ready(timeout: int = 90) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            # v8 removed /ui-bootstrap; /projects is a cheap authed probe
            if requests.get(f"{ADMIN}/projects", headers=H, timeout=5).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(2)
    sys.exit("Unleash did not become ready")


def delete_flag(name: str) -> None:
    """Archive, then permanently delete, so reseeding is idempotent."""
    requests.delete(f"{ADMIN}/projects/default/features/{name}", headers=H, timeout=10)
    requests.delete(f"{ADMIN}/archive/{name}", headers=H, timeout=10)


def create_flag(name: str, ftype: str) -> None:
    r = requests.post(f"{ADMIN}/projects/default/features", headers=H,
                      json={"name": name, "type": ftype}, timeout=10)
    if r.status_code not in (200, 201):
        sys.exit(f"create {name} failed: {r.status_code} {r.text[:200]}")


def enable_in_dev(name: str) -> None:
    """Turn the flag ON in development: add a 100% default strategy, then
    toggle the environment on. Verified against Unleash v8."""
    r = requests.post(
        f"{ADMIN}/projects/default/features/{name}/environments/development/strategies",
        headers=H,
        json={"name": "default", "parameters": {}, "constraints": []},
        timeout=10,
    )
    if r.status_code not in (200, 201):
        sys.exit(f"strategy for {name} failed: {r.status_code} {r.text[:200]}")
    r = requests.post(
        f"{ADMIN}/projects/default/features/{name}/environments/development/on",
        headers=H, timeout=10,
    )
    if r.status_code not in (200, 201):
        sys.exit(f"env-on for {name} failed: {r.status_code} {r.text[:200]}")


TOKEN_FILE = pathlib.Path(__file__).resolve().parent.parent / "audit" / "unleash_client_token"


def ensure_client_token() -> str:
    """Create (or reuse) a backend token for the traffic simulator SDK.

    INIT_*_TOKENS env vars only apply on first boot with an empty DB, and
    Unleash generates the secret server-side, so we create via API and persist
    the secret for simulate_traffic.py to read. Returns the secret.
    """
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    r = requests.post(
        f"{ADMIN}/api-tokens",
        headers=H,
        json={
            "tokenName": "traffic-sim",
            "type": "backend",
            "environment": "development",
            "projects": ["default"],
        },
        timeout=10,
    )
    if r.status_code not in (200, 201):
        sys.exit(f"token creation failed: {r.status_code} {r.text[:200]}")
    secret = r.json()["secret"]
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(secret + "\n")
    return secret


def main() -> None:
    wait_ready()
    ensure_client_token()
    print("Seeding Unleash with the demo flag matrix...")
    for name, ftype, live, expected in FLAGS:
        delete_flag(name)
        create_flag(name, ftype)
        if live:
            enable_in_dev(name)
        print(f"  {name:<22} type={ftype:<10} live={str(live):<5} expected: {expected}")
    print("Done. Start traffic with: make traffic  (background)")
    print(f"Seeded at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
