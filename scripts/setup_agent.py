#!/usr/bin/env python3
"""Configure the TrueForge model provider (optional) and create the saved
'flag-reaper' agent with the gate wired in.

Usage:
  # once you have an API key for any catalog provider (e.g. Z.ai, Anthropic, OpenAI):
  python scripts/setup_agent.py --provider zai --api-key sk-...
  python scripts/setup_agent.py --list-providers
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request

BASE = "http://localhost:8790/api/v1"


def _req(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:300]}", file=sys.stderr)
        sys.exit(1)


AGENT_SPEC = {
    "model": {"name": "PLACEHOLDER"},  # filled from --model
    "instructions": (
        "You are the Feature Flag Reaper. You hunt zombie feature flags by "
        "following the reaper-runbook skill EXACTLY. The pipeline is bounded "
        "and deterministic: classify_flags → evidence → apply_and_test only "
        "for REMOVABLE flags → open_pr only after tests pass. NEVER merge. "
        "For UNKNOWN flags, ask the human the question and wait for the "
        "answer before calling answer_unknown. Never guess, never fabricate "
        "evidence, never merge."
    ),
    "mcp_servers": [
        {
            "name": "reaper",
            "enable_tools": ["@all"],
            # Gate by explicit tool name: unannotated FastMCP tools bypass
            # @destructive matching (verified in docs + M0).
            "require_approval_for_tools": ["open_pr", "apply_and_test"],
        }
    ],
    "skills": [{"name": "reaper-runbook"}],
    "config": {
        "sandbox": {"enabled": True},
        "generative_ui": {"enabled": True},
        "ask_user_questions": {"enabled": True},
        "dynamic_sub_agents": {"enabled": True},
        "iteration_limit": 100,
    },
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", help="catalog provider id, e.g. zai / anthropic / openai")
    ap.add_argument("--api-key", help="API key for the provider")
    ap.add_argument("--model", default=None,
                    help="model FQN for the agent (default: provider default)")
    ap.add_argument("--list-providers", action="store_true")
    args = ap.parse_args()

    if args.list_providers:
        cat = _req("GET", "/catalogs/model-providers")
        for p in cat.get("data", []):
            print(" -", p.get("id") or p.get("name"), "|", (p.get("displayName") or ""))
        return

    if args.provider and args.api_key:
        body = {"providerId": args.provider, "apiKey": args.api_key}
        # provider-specific secret field names live in the catalog manifest;
        # the UI does the same via Settings → Models.
        try:
            resp = _req("POST", "/settings/model-providers", body)
            print("provider configured:", json.dumps(resp)[:200])
        except SystemExit:
            print("trying alternate payload shape...")
            resp = _req("POST", "/settings/model-providers",
                        {"provider": args.provider, "apiKey": args.api_key})
            print("provider configured:", json.dumps(resp)[:200])

    models = _req("GET", "/models")
    configured = models.get("data", [])
    if not configured:
        print("No model provider configured in TrueForge yet.\n"
              "Open http://localhost:8790 → Settings → Models, or rerun with "
              "--provider/--api-key.", file=sys.stderr)
        sys.exit(2)

    model_name = args.model or configured[0].get("name") or configured[0].get("id")
    if "/" not in str(model_name):
        model_name = f"{configured[0].get('provider', '')}/{model_name}"
    spec = dict(AGENT_SPEC)
    spec["model"] = {"name": model_name}
    print("creating agent with model:", model_name)
    resp = _req("POST", "/agents", {
        "name": "flag-reaper",
        "description": "Feature Flag Reaper — hunts zombie feature flags; "
                       "never merges; asks on every unknown.",
        "manifest": spec,
    })
    print("agent created:", json.dumps(resp.get("data", resp))[:300])
    print("\nReady: open http://localhost:8790 → Agents → flag-reaper → Try")


if __name__ == "__main__":
    main()
