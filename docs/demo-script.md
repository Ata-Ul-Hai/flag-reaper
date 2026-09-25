# Demo script — 2–3 min video & live run

## Setup (before recording / before the audience arrives)

```bash
make demo-reset     # fresh Unleash flags, clean demo repo, empty audit log
make traffic &      # background: real metrics flowing
make scan           # pre-warm: verify the exact 8 verdicts
make mcp            # reaper MCP server on :8900
scripts/run_trueforge.sh
# open http://localhost:8790 → Agents → flag-reaper → Try
# open the /report view in a second tab: http://127.0.0.1:8900/report
```

Rehearse TWICE. Only 1–2 PRs are opened live (TrueForge re-prompts approval
per call — that's a feature in the story, but don't do six of them).

## The arc

1. **Hook (15s).** "Teams accumulate hundreds of feature flags. Nobody deletes
   them, because nobody can prove they're dead. Deleting a flag is
   irreversible — you'd have to prove it gets no traffic, has no code
   references, and that removing it breaks nothing. That's three systems.
   Today an agent does that correlation — and stops exactly where it should."

2. **Scan (30s).** In TrueForge chat: "Run the reaper on the checkout
   service." The agent calls `classify_flags`. Show the summary: 3 REMOVABLE,
   3 STILL_LIVE, 2 UNKNOWN.

3. **Evidence (30s).** Ask for evidence on `new-checkout-flow`: path:line
   grep hits, lastSeenAt, last-hour count. Maybe show `beta-search-ranking`
   in config/flags.yaml — "found in a config map — that's why it's unknown."

4. **The removal + PR (30s).** "Remove new-checkout-flow." Agent calls
   `apply_and_test` (approval pause #1 — allow), tests pass, then `open_pr`
   (approval pause #2 — allow). Show the PR: evidence section, the diff with
   the branch-survival note, the rollback line, "this agent cannot merge."

5. **The gate (40s).** "What about `exp_checkout`?" The agent asks the human:
   "constructed at runtime in app/flags.py:38 — is it still in use?" Answer
   "dead" → agent calls `answer_unknown` → flag becomes REMOVABLE (plan-only).
   **Never show it merging autonomously.**

6. **Close (15s).** Architecture slide: bounded pipeline, three deterministic
   LLM touchpoints, append-only audit (`GET /audit`), and the line: "the one
   line it will not cross: the merge."

## Build story (post during the build)

Post on LinkedIn/X tagging @truefoundry and @polariscodes. Angle: "I built an
agent whose whole personality is refusing to guess." Include: the SSRF
allowlist gotcha for local MCP servers, the branch-survival rule, the harness
approval pause screenshots, and the audit trail screenshot.
