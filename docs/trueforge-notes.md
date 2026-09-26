# TrueForge — M0 Hands-On Findings

> Verified 26 Sep 2026 against TrueForge **v0.2.1** running locally on macOS
> (npx standalone mode). All findings below were confirmed by running the
> server and calling its API — not from docs alone.

## 1. Startup facts

- `npx -y @truefoundry/trueforge@latest` → server + chat UI at
  `http://localhost:8790`, OpenAPI at `/api/v1/openapi.json`, Swagger UI at
  `/api/v1/docs`. Node 26 worked (docs say ≥22.14).
- Standalone mode: SQLite at
  `~/Library/Application Support/trueforge/db/db.sqlite`, no auth, localhost only.
- Startup log line: **"Local sandbox fallback is available"** (darwin, bash,
  python3.14) — a local sandbox fallback exists in v0.2.1 even though the docs
  and catalog list only Daytona.

## 2. SSRF guard blocks localhost MCP servers (critical gotcha)

Registering `http://127.0.0.1:8765/mcp` failed with:
`Outbound URL blocked for host "127.0.0.1"`.

Root cause (read from `trueforge-core/dist/core/util/ssrfGuard.js`): the guard
denies loopback/private CIDRs and dotless/suffixed hosts, with two config
knobs wired from env (found in `trueforge/dist/main.js`):

```bash
# JSON string array. Allowlists hosts, bypassing private-IP checks for them.
export OUTBOUND_URL_ALLOWED_HOSTS='["127.0.0.1","localhost"]'
# optional: disable the guard entirely (do NOT use; keep guard on)
# export NETWORK_POLICY_ENABLED=false
```

With `OUTBOUND_URL_ALLOWED_HOSTS` set, registration and tool listing both work.
The guard stays on for all other hosts. This env var is required for the whole
project — see `scripts/run_trueforge.sh`.

## 3. MCP servers: remote-URL only, Python FastMCP verified

- Catalog + API accept `type: "remote"` manifests only (no stdio transport).
- A **Python FastMCP** server (`mcp.run(transport="http", ...)`) on localhost
  streamable HTTP registers cleanly:

```bash
curl -X PUT http://localhost:8790/api/v1/settings/mcp-servers \
  -H 'Content-Type: application/json' \
  -d '{"manifest":{"type":"remote","name":"reaper-test",
        "url":"http://127.0.0.1:8765/mcp","description":"test"}}'
# → {"data":{"name":"reaper-test","auth_status":{"status":"not_required"}}}
curl http://localhost:8790/api/v1/mcp-servers/reaper-test/tools   # lists tools
```

- Tool list endpoints: `GET /api/v1/mcp-servers/{name}/tools`.
- No DELETE route on settings (POST=create, PUT=update); UI can remove.

## 4. Approvals / human checkpoints (the gate)

From the live OpenAPI (`AgentSpec → mcp_servers[]`):

```json
{
  "name": "reaper",
  "enable_tools": ["@all"],
  "require_approval_for_tools": ["open_pr", "apply_and_test"]
}
```

- `require_approval_for_tools` default is `["@destructive"]`, but that only
  matches tools the MCP server annotates (`@write`/`@destructive` hints).
  FastMCP tools are unannotated → **always gate by explicit tool name**.
- Matching calls pause the turn until a human Allow/Deny in chat.
- `ask_user_questions` (default on) = the UNKNOWN-flag mechanism.
- `generative_ui` (default on) = evidence cards in chat.
- **No approve-once yet** — every matching call re-prompts. Demo with 1–2 PRs.

## 5. Agent creation API (saved agents)

`POST /api/v1/agents` with `{name, description, manifest: AgentSpec}`:

```json
{
  "model": {"name": "provider/model"},
  "instructions": "...",
  "mcp_servers": [{"name": "reaper", "require_approval_for_tools": ["open_pr"]}],
  "skills": [{"name": "reaper-runbook"}],
  "config": {"sandbox": {"enabled": true}}
}
```

- Model FQN is `provider/model`. Model provider catalogs show native support
  for OpenAI, Anthropic, Google, Fireworks, **Z.ai**, Moonshot, Together,
  Alibaba, TrueFoundry gateway, and custom OpenAI-compatible endpoints.
- Sessions: `POST /api/v1/sessions` (`agent: {name}` or inline `agent.spec`),
  turns stream via SSE; Python SDK `trueforge_sdk` is a pure API client.

## 6. Skills

`POST /api/v1/settings/skills` with `SkillManifest`; `type: "git"` requires a
GitHub/GitLab HTTPS URL (API regex-enforced: `https://github.com/owner/repo`),
optional `path` (skill dir inside the repo) and `ref` (branch/tag/SHA).
**Local folders cannot be imported** → the reaper skill must be pushed to
GitHub. Skills need `config.sandbox.enabled: true` on the agent; they clone
into the sandbox at `/opt/tfy/skills/{name}`.

## 7. Sandbox

- Catalog lists only Daytona (`/api/v1/catalogs/sandbox-providers`), needing an
  API key with sandbox + snapshot-create permissions.
- BUT v0.2.1 logs **"Local sandbox fallback is available"** on macOS → code
  execution appears to work without Daytona in standalone mode (to be exercised
  in M3; if it works, Daytona is optional for the live demo and only a "cloud
  sandbox" flourish).
- Sandbox-as-tool: loop stays on the server; skills/Code Mode require the
  sandbox; MCP calls from in-sandbox scripts are bridged back through the
  harness (approvals still enforced).

## 8. Known bug: TrueForge crashes when a connected MCP server dies

Verified 26 Sep: killing the local reaper MCP server while TrueForge was
running crashed the entire TrueForge process — its MCP client retried the
broken streamable-HTTP connection and hit an
`UnhandledPromiseRejection` in `StreamableHTTPClientTransport._scheduleReconnection`
(Node 26 treats unhandled rejections as fatal). Symptom in the browser:
"Something went wrong — Failed to fetch" on turn submit.

Rule: **never restart the reaper server while TrueForge is running — or
restart TrueForge right after.** `make stack` starts both in the safe order.
Worth reporting upstream (github.com/truefoundry/trueforge issues).

## 9. Implications for the build

1. Always start TrueForge via `scripts/run_trueforge.sh` (sets the allowlist).
2. Reaper = FastMCP Python server on `127.0.0.1:8900/mcp`, registered as
   `reaper`, approved tools named explicitly.
3. Skill repo must be pushed to GitHub; import via Settings → Skills or API.
4. Gate = TrueForge chat (approvals + ask-user); backup = thin `/report`
   + `/audit` routes on the reaper server.
5. Test the local sandbox fallback early in M3; wire Daytona only if trivial.
