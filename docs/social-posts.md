# Social posts — #agentsthatact (all verified ≤ 280 chars)

The original launch tweet + reply were delivered in chat earlier. Post these
three as a fresh follow-up thread (or standalone tweets) for cadence through
Monday 28 Sep 11:59 PM (social prize deadline). Best order: 1 → 2 → 3, spaced
a few hours apart.

## Post 1 — build update (277 chars)

Feature Flag Reaper update (#agentsthatact, built with @truefoundry):

Every cleanup goes through:
• real Unleash traffic signals
• ripgrep tracing with file:line evidence
• a classifier that never guesses
• pytest before any patch ships

Then it stops at the merge. By design.

## Post 2 — upstream bug report (263 chars)

Filed my first upstream bug too 👇

While running the agent, the TrueForge harness crashed when a registered MCP server went down — unhandled rejection in the reconnection path.

Isolated it, reported it:
github.com/truefoundry/trueforge/issues/878

#agentsthatact

## Post 3 — how it's built on TrueForge (262 chars)

How Feature Flag Reaper runs on TrueForge:

• reaper core = deterministic MCP tools: inventory → trace → classify → plan → apply+test → PR
• the agent follows a git-backed skill
• open_pr pauses for human approval
• the agent's token cannot merge

#agentsthatact
