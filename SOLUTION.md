# Solution Writeup — Feature Flag Reaper

**The problem.** Engineering teams accumulate hundreds of feature flags. Each
stale one is a permanent branch of untested code living in production paths.
Vendors know it — Unleash ships a "stale" marker — but marking debt is where
the industry stops, because deleting a flag is irreversible: proving one is
truly dead requires correlating three systems — the flag service (traffic),
the codebase (references), and the test suite (behavior).

**What the agent reaches.** The Feature Flag Reaper connects to a real
self-hosted Unleash instance and traces a real git repo with ripgrep. It
classifies every flag into REMOVABLE / STILL_LIVE / UNKNOWN with path:line
evidence, including deterministic detection of dynamically-constructed flag
keys (f-strings, string concat, config-map lookups). For provably-dead flags it
applies the removal on a disposable copy, runs the test suite, and — only if
green — opens a cleanup PR with evidence, the diff, and a rollback note.

**Where it stops.** Three hard stops. (1) UNKNOWN flags — keys built at
runtime — trigger an ask-user question in chat; the agent cannot proceed
without a human answer. (2) `open_pr` and `apply_and_test` require harness-level
approval: TrueForge pauses the turn until a human clicks Allow. (3) The merge:
the agent never merges, and cannot — its GitHub token is fine-grained with
Contents + Pull-requests write only, no merge scope.

**Architecture.** A bounded, deterministic pipeline — not an autonomous LLM
loop. The reaper core is a Python MCP tool server (FastMCP) exposing eight
tools (`classify_flags`, `trace_references`, `apply_and_test`, `open_pr`,
`answer_unknown`, …); every call appends to an append-only JSONL audit log.
A git-backed skill (reaper-runbook) pins the exact procedure; the TrueForge
agent wires the tools, skill, approvals, sandbox, and chat UI.

**How TrueForge was used.** TrueForge runs the agent loop, the chat UI, the
generative-UI evidence cards, ask-user pauses, and tool approvals
(`require_approval_for_tools` on the two state-changing tools). Code execution
runs in TrueForge's sandbox. TrueForge local mode (npx, SQLite) drives the
entire demo.

**Real vs mocked.** Everything is real: Unleash 8.2 in Docker with real Admin
API calls and real client-SDK metrics; a real git repo scanned with ripgrep;
real pytest runs; real GitHub PRs (links in the README). The demo repo is
seeded to guarantee a good demo — the pipeline itself works on any repo + any
Unleash instance.

**Known limits.** Evaluation metrics are last-hour + lastSeenAt recency (OSS
Unleash doesn't expose long historical windows). The patcher handles trivial
literal flag-check shapes; complex call sites are conservatively reported as
STILL_LIVE. One flag provider (Unleash). One PR per flag.
