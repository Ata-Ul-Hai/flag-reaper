# Feature Flag Reaper

An agent that hunts **zombie feature flags** — built on
[TrueForge](https://github.com/truefoundry/trueforge) for the
*Agents That Act: TrueFoundry × Polaris Hackathon* (26 Sep 2026, Bangalore).

It connects to a real **Unleash** instance, traces a real **git repo** with
ripgrep, classifies every flag into **REMOVABLE / STILL_LIVE / UNKNOWN** with
evidence, sandbox-tests removals and opens evidence-backed cleanup PRs — and
**stops to ask a human on every unknown**. It never merges: the GitHub token
has no merge scope, by design.

> The demo isn't "an agent that tidies flags" — it's the hardest problem in
> agentic automation made visible: acting decisively where safety is provable,
> refusing where it isn't, with the audit trail to show for it.

## Architecture

```
 TrueForge (localhost:8790)  — agent loop, chat UI, approvals, sandbox
   ├── MCP server "reaper" (FastMCP, Python, 127.0.0.1:8900/mcp)
   │     inventory_flags   trace_references   classify_flags
   │     plan_removal      apply_and_test*    open_pr*
   │     get_report        answer_unknown
   │     (* require harness-level human approval — the turn pauses)
   │     every call → append-only audit log (audit/audit.jsonl)
   ├── Skill "reaper-runbook" (git repo) — pins the bounded procedure
   └── Agent "flag-reaper": approvals on open_pr/apply_and_test,
         ask-user on UNKNOWN, generative-UI evidence cards, sandbox on
```

Determinism lives inside the tools; the skill pins the tool order; the LLM's
only freeform job is narration. No autonomous planning loop.

## The demo matrix (8 seeded flags → exact expected verdicts)

| flag | code shape | traffic | verdict |
|---|---|---|---|
| `legacy-coupon-banner` | no references | 0 | REMOVABLE (flag-only) |
| `darkmode-toggle` | test files only | 0 | REMOVABLE (tests + flag) |
| `new-checkout-flow` | trivial if/else, default off | 0 | REMOVABLE (code + flag) |
| `recommendation-v2` | multiple call sites, expressions | 0 | STILL_LIVE (rule 6) |
| `checkout-redesign` | trivial if/else | live sim | STILL_LIVE (traffic) |
| `spring-campaign` | literal | live sim | STILL_LIVE (traffic) |
| `exp_checkout` | `f"exp_{name}"` | 0 | UNKNOWN (dynamic) |
| `beta-search-ranking` | YAML config-map lookup | 0 | UNKNOWN (dynamic) |

## Quickstart

```bash
make install        # python deps
make unleash        # Unleash 8.2 + Postgres on :4242
make seed           # seed the 8-flag matrix (idempotent)
make traffic &      # real Unleash SDK pushing real metrics (background)
make scan           # → the exact 8 verdicts
make mcp            # reaper MCP server on :8900 (+ /report /audit views)
scripts/run_trueforge.sh   # TrueForge on :8790 (SSRF allowlist for local MCP)
python scripts/setup_agent.py   # creates the saved agent (needs a model key)
```

Then open http://localhost:8790 → Agents → **flag-reaper** → Try, and say:
"Run the reaper on the checkout service."

`make demo-reset` restores the entire demo to a clean state in one command.

## Verdict rules (ordered, first match wins)

0. flag younger than `min_age_hours` → **SKIP**
1. recent `lastSeenAt` or last-hour evaluations > 0 → **STILL_LIVE**
2. dynamic construction (f-string / concat / config map) → **UNKNOWN → ask**
3. no references → **REMOVABLE** (flag-only)
4. only test references → **REMOVABLE** (tests + flag)
5. literal refs, trivially patchable → **REMOVABLE** (code + flag)
6. anything else → **STILL_LIVE** (conservative)

Patching keeps the branch matching the flag's current default value
(branch-survival rule), runs the test suite on a disposable copy, and only a
green run may proceed to a PR. A red run downgrades to plan-only.

## Honesty note

On a fresh Unleash, "zero evaluations in the last hour" and `lastSeenAt: null`
mean exactly that — zero since metrics began. The reaper never fabricates
historical usage; the traffic simulator (`make traffic`) generates *real*
metrics through the real SDK → `/api/client/metrics` → Admin API pipeline.

## Repo layout

See [AGENT.md](AGENT.md) (source of truth) and
[docs/trueforge-notes.md](docs/trueforge-notes.md) (verified TrueForge v0.2.1
integration details, including the SSRF-allowlist requirement for local MCP
servers).
