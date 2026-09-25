#!/usr/bin/env bash
# Start TrueForge with the config the reaper needs:
#  - OUTBOUND_URL_ALLOWED_HOSTS: the SSRF guard blocks loopback MCP URLs by
#    default; this allowlists the local reaper MCP server while keeping the
#    guard on for everything else (verified in docs/trueforge-notes.md).
set -euo pipefail
export OUTBOUND_URL_ALLOWED_HOSTS='["127.0.0.1","localhost"]'
exec npx -y @truefoundry/trueforge@latest
