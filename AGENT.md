# FEATURE FLAG REAPER — Master Build Brief (v2)

> This document is the source of truth for the project. If a decision changes,
> update this file. Changes from v1 are marked **[v2]** with the reason.

---

## 1. What we're building

An agent that hunts **zombie feature flags**: connects to a real flag service
(Unleash, self-hosted), traces a real git repo for code references, classifies
each stale flag, drafts removal PRs for provably-dead ones, and **stops and asks
a human** whenever it can't prove safety. The agent never merges, never guesses.

**Built for:** "Agents That Act: TrueFoundry × Polaris Hackathon" — Bangalore,
26 Sep 2026, ₹3,00,000 pool. Round 2 is a single 7-hour in-person build day;
demos + prizes the same night. **Pre-building before the event is explicitly
invited by the organizers** ("runs locally with one command, so you can start
today" — Luma page). Everything is built and rehearsed before arrival; the build
day is for deepening integration and polishing.

**Judges verify all four of these in the final submission:**
1. A **real tool reached** (actual API integration, not a mock)
2. **Code run in a sandbox** (the agent executes its own change safely)
3. A **pause before anything irreversible** (human gate)
4. Built **on TrueForge**, TrueFoundry's open-source agent harness

**Problem statement (final):**
> Feature flag debt is invisible risk that compounds. Every mature team
> accumulates hundreds of flags; each stale one is a permanent branch of
> untested code living in production paths. Vendors know it — Unleash ships a
> "stale" marker — but marking debt is where the industry stops, because
> deleting a flag is irreversible: proving one is truly dead requires
> correlating three systems — the flag service (traffic), the codebase
> (references), and the test suite (behavior).
> The Feature Flag Reaper completes that loop: real Unleash, real git, verdicts
> with evidence, sandboxed removal with green tests, a PR you approve — and a
> structural stop on every unknown. It never merges; the PAT can't.
> **Acting decisively where safety is provable, refusing where it isn't — with
> the audit trail to show for it.**

**Registered Round-1 description (naming must stay consistent):**
> A Feature Flag Reaper that hunts zombie feature flags. It reaches a real flag
> service (Unleash) for inventory and usage metrics, and traces a real git repo
> with ripgrep. Each stale flag gets classified: safely removable, still-live,
> or unknown. For removable flags it applies the removal in a sandbox, runs the
> test suite, then drafts a cleanup PR with evidence and a rollback note. The
> gate is the merge: it never merges itself and stops to ask on every unknown.

---

## 2. Core design principle

**A bounded, deterministic pipeline — NOT an autonomous LLM loop.**

Determinism lives inside the MCP tools (fixed code). TrueForge runs the agent
loop, but the **reaper skill** pins the procedure: exact tool order, exact rules,
"never guess — ask." The LLM's freeform work is narration and PR prose only.
Dynamic-key detection is deterministic (regex + rules), not an LLM job. **[v2]**
(LLM jobs 2–3 from v1 — evidence narration, PR body — are now done by the
TrueForge agent itself, which is literally the model in the loop; this removes
one bespoke LLM integration without weakening determinism.)

---

## 3. Locked decisions

| Decision | Choice |
|---|---|
| Flag service | Self-hosted **Unleash** (Docker + Postgres, pinned tag, `INIT_ADMIN_API_TOKENS` — `AUTH_TYPE=none` is deprecated **[v2, verified]**) |
| Reference tracing | Local `git clone` + **ripgrep** |
| Harness | **TrueForge** v0.2.x via `npx @truefoundry/trueforge` — architecture verified hands-on **[v2]** |
| Core language | **Python** (FastMCP server; harness language is irrelevant to us) **[v2, verified]** |
| PR creation | GitHub REST via PyGithub; private demo repo + fine-grained PAT (Contents + PR write, **no merge scope**) |
| Staleness signals | **`lastSeenAt` recency + last-hour metrics + simulated live traffic** — NOT a 60-day historical window (OSS Unleash doesn't reliably expose historical usage; `lastSeenAt` = last metrics collection, documented) **[v2, verified]** |
| Gate | **The merge.** Double gate: PAT has no merge scope AND `open_pr` requires TrueForge harness approval |
| Gate surface | **TrueForge native** (tool approval + ask-user-questions + generative UI in chat). Thin FastAPI `/report` + `/audit` page as demo backup only **[v2]** |
| Skill repo | Must be a **GitHub/GitLab HTTPS URL** (API-enforced regex) → push `skill/` to GitHub **[v2, verified]** |

---

## 4. Architecture **[v2 — reframed around TrueForge's real shape]**

```
 TrueForge (localhost:8790)  — agent loop, chat UI, approvals, sandbox
   │ attaches
   ├── MCP server "reaper" (FastMCP, Python, http://127.0.0.1:8900/mcp)
   │     inventory_flags      → Unleash Admin API: flags + lastSeenAt + last-hour metrics
   │     trace_references     → ripgrep over demo repo: literal/test/dynamic kinds
   │     classify_flags       → ordered rules (§5), verdict + evidence per flag
   │     plan_removal         → diff preview + tier decision
   │     apply_and_test       → sandbox: apply patch + run tests (local fallback)
   │     open_pr              → PyGithub branch/commit/PR   [REQUIRES APPROVAL]
   │     get_report           → full verdict report (also drives generative-UI cards)
   │     answer_unknown       → records human answer, reclassifies that flag
   │     every tool call → append-only audit log (JSONL)
   ├── Skill "reaper-runbook" (git repo: SKILL.md + scripts/) — pins the procedure
   └── Agent "flag-reaper": model + skill + MCP + config:
         require_approval_for_tools: ["open_pr", "apply_and_test"]
         ask_user_questions: true (UNKNOWN gate), generative_ui: true,
         sandbox: true
```

**TrueForge startup env (required, verified in M0):**
`OUTBOUND_URL_ALLOWED_HOSTS='["127.0.0.1","localhost"]'` — the SSRF guard
blocks loopback MCP URLs by default; this allowlists local MCP servers while
keeping the guard on for everything else.

---

## 5. Classifier — ordered rules, first match wins

Signals per flag: `lastSeenAt` recency + last-hour evaluations (Unleash), code
references (ripgrep), reference kind (literal / test-file / dynamic).

| # | Condition | Verdict |
|---|---|---|
| 0 | flag created < `--window-days` ago | SKIP — too young |
| 1 | lastSeenAt recent (≤ window) OR last-hour traffic > 0 | STILL_LIVE |
| 2 | any reference is DYNAMIC (deterministic detection: f-string, concat, config-map lookup) | UNKNOWN → stop & ask |
| 3 | no references at all | REMOVABLE (flag-only delete) |
| 4 | references only in test files | REMOVABLE (tests + flag) |
| 5 | all references literal & trivial | REMOVABLE (code patch + flag) |
| 6 | any other references exist | STILL_LIVE (report only — conservative) |

Dynamic construction patterns (regex pre-pass, no LLM): `f"...{...}..."`,
string concat near the call, dict/list lookup near the call (e.g. YAML config
map keyed lookup), `getattr`/`vars()` near the call.

---

## 6. Removal rules

**Trivial literal pattern** = flag key appears as a plain string literal passed
to the flag-check call, used as a direct if-condition or ternary.

**Branch survival rule:** when patching an if/else, keep the branch matching the
flag's **current default evaluation value** from Unleash (off → keep the
else/default branch). Stated in the PR body.

**Tier 1 (auto-patch):** rules 3, 4, 5. Apply diff → run test suite → only if
green, `open_pr`. If red → downgrade to plan-only with test output attached.
**Tier 2 (plan-only PR):** justified but non-trivial patch or tests failed.

**Every PR contains:** verdict + evidence (`path:line` grep snippets, traffic
stats, lastSeenAt), flag key + default value, one-line rollback note
(`git revert <sha>`). Branch: `reaper/remove-<flag-key>`. One flag per PR.

---

## 7. The Gate **[v2]**

**Primary = TrueForge chat UI** (verified primitives):
- Tool approval: turn pauses on `open_pr` / `apply_and_test` until a human
  clicks Allow/Deny. Enforced by the harness — "cannot, not chooses not to."
- UNKNOWN: agent uses ask-user-questions with the evidence-backed question;
  the human's answer flows back via `answer_unknown`, which reclassifies and
  resumes exactly that flag.
- Generative UI: `get_report` output renders as evidence cards in chat.
- **No "approve once" yet in TrueForge** — each gated call re-prompts. Demo
  accordingly: create only 1–2 PRs live.

**Backup = thin FastAPI** in the reaper server: `GET /report` (verdict table +
expandable evidence), `GET /audit` (full JSONL trail). Used only if the chat
flow misbehaves on stage. No approve endpoints here — the gate lives in chat.

**Append-only audit log** (`audit/audit.jsonl`): every agent action and human
decision, `{ts, actor: agent|human|trueforge, action, payload}`.

---

## 8. Seed demo repo — `demo/checkout-service`

Unchanged from v1: 8 flags with exact code shapes →
3 REMOVABLE (`legacy-coupon-banner`, `darkmode-toggle`, `new-checkout-flow`),
3 STILL_LIVE (`recommendation-v2`, `checkout-redesign`, `spring-campaign`),
2 UNKNOWN (`exp_checkout` via f-string, `beta-search-ranking` via YAML map).

Traffic simulation: `scripts/simulate_traffic.py` uses the real `UnleashClient`
SDK so metrics genuinely flow through the real pipeline; run in background
during the demo. **Honesty note in README:** on fresh Unleash, "zero
evaluations" means zero since metrics began — documented, never fabricated.
`make demo-reset` re-seeds everything for repeatable demos.

---

## 9. Repo layout **[v2]**

```
flag-reaper/
  AGENT.md                  # this file
  reaper/
    inventory.py tracer.py classify.py dynamic_detect.py
    remover.py prs.py audit.py report.py
    server.py               # FastMCP tool server (+ /report /audit backup routes)
  skill/
    SKILL.md                # reaper-runbook — the pinned procedure
    scripts/                # executed inside the sandbox (apply_and_test)
  server/backup_dashboard.py  # thin FastAPI backup (report + audit only)
  scripts/seed_unleash.py simulate_traffic.py run_trueforge.sh
  demo/checkout-service/    # seed repo (own git repo)
  docs/trueforge-notes.md   # M0 hands-on findings
  docs/demo-script.md       # 2-3 min video + live demo script
  audit/audit.jsonl
  docker-compose.unleash.yml
  Makefile                  # demo-reset, scan, serve, mcp
  README.md
```

---

## 10. Milestones

M0 ✅ **done** (hands-on TrueForge spike — see `docs/trueforge-notes.md`).
Key finds: SSRF guard blocks loopback MCP URLs (fix: `OUTBOUND_URL_ALLOWED_HOSTS`);
FastMCP registration + tool listing verified end-to-end; agent/skill/approval
API schemas captured; local sandbox fallback exists on darwin (Daytona optional
for local dev — still nice for the "cloud sandbox" story).

M1 Unleash up + seeded + inventory tool. Done when `make scan` prints the
inventory table with traffic + lastSeenAt.

M2 Tracer + classifier. Done when the 8-flag matrix produces exact expected
verdicts with `path:line` evidence.

M3 Sandbox removal + tests. Done when `new-checkout-flow` removal passes tests
end-to-end AND a deliberately broken patch downgrades to plan-only.

M4 PR generation via PyGithub (approval-gated). Done when a real PR exists on
the demo repo, correctly formatted.

M5 Gate + audit wiring in TrueForge. Done when an UNKNOWN question asked in
chat unblocks exactly that flag via `answer_unknown`, and the audit trail shows
every step.

M6 Demo polish: README + diagram, `make demo-reset`, video script, build-story
post (LinkedIn/X, tag @truefoundry @polariscodes — ₹50k/₹25k story prizes are
open to all Round-1 registrants), rehearse 2–3×.

---

## 11. Demo script

See `docs/demo-script.md`. Arc: hook (flag debt) → scan (8 flags) → evidence
cards → approve an auto-PR in chat → UNKNOWN gate stops and asks → answer →
resume → audit trail → "the one line it will not cross: the merge."

---

## 12. Hard constraints

1. **No faked results.** Pipeline works on any repo + Unleash; the seed repo
   guarantees a good demo but is not a mock.
2. **Never merge.** Not via API, not via PAT scope.
3. **Never guess on UNKNOWN.** Ask, wait, resume only on a human answer.
4. **No autonomous LLM loop.** Determinism lives in the tools; the skill pins
   the procedure; narration is the LLM's only freeform job.
5. **Scope discipline.** No auth/multi-tenancy, no flag creation, no dashboard
   beyond the backup report/audit, one flag provider. Finish narrow and deep.
6. **Keep AGENT.md updated** as decisions change.

---

## 13. Prerequisites checklist (owner: user)

- [x] Node ≥ 22.14, Docker running, ripgrep, Python 3.13 (all verified on this Mac)
- [ ] Round-2 invitation confirmed (email/Discord) + kickoff time noted
- [ ] Model API key configured in TrueForge Settings → Models
- [ ] Private GitHub repo `flag-reaper-demo` (or similar) + fine-grained PAT:
      Contents + Pull requests write, **no merge scope**
- [ ] Skill repo on GitHub (push `skill/`; any GitHub repo URL works)
- [ ] Daytona account + key (Sandbox + Snapshot-write) — **optional for local
      dev** (local sandbox fallback exists), but recommended for the "cloud
      sandbox" judging story
