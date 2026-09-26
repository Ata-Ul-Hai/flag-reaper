# Social posts for #agentsthatact (all X posts verified at 280 chars or fewer)

The launch tweet and its reply were delivered in chat earlier. Post the three
X updates below as a fresh follow-up thread for cadence through Monday 28 Sep
11:59 PM (social prize deadline). Best order: 1 then 2 then 3, spaced a few
hours apart. The LinkedIn post is a single standalone post.

## Post 1. Build update (277 chars)

Feature Flag Reaper update (#agentsthatact, built with @truefoundry):

Every cleanup goes through:
• real Unleash traffic signals
• ripgrep tracing with file:line evidence
• a classifier that never guesses
• pytest before any patch ships

Then it stops at the merge. By design.

## Post 2. Upstream bug report (263 chars)

Filed my first upstream bug too 👇

While running the agent, the TrueForge harness crashed when a registered MCP server went down. Unhandled rejection in the reconnection path.

Isolated it, reported it:
github.com/truefoundry/trueforge/issues/878

#agentsthatact

## Post 3. How it runs on TrueForge (262 chars)

How Feature Flag Reaper runs on TrueForge:

• reaper core = deterministic MCP tools: inventory → trace → classify → plan → apply+test → PR
• the agent follows a git-backed skill
• open_pr pauses for human approval
• the agent's token cannot merge

#agentsthatact

## LinkedIn post (single standalone post, no length issue)

Copy the text between the lines. In the LinkedIn composer, manually tag the
TrueFoundry and Polaris pages by typing @ and their names where the two
mentions appear below. Post 2 of the X thread references the same issue, so
posting the LinkedIn version first and the X thread after works fine.

---

I built an agent that cleans up dead feature flags. And it refuses to merge anything.

Here is how Feature Flag Reaper got built for Agents That Act, the hackathon by @TrueFoundry and @Polaris.

The problem is boring and expensive. Teams ship feature flags behind if statements, forget to remove them, and a year later nobody knows which ones are safe to delete. Deleting a live flag breaks production. Guessing is not an option.

So I made guessing impossible. The agent only ever says three things:

REMOVABLE. No live code references, zero recent traffic.
STILL_LIVE. It sees real traffic or live references.
UNKNOWN. It cannot prove either way, so it stops and asks a human.

That third one is the whole product.

How it works. The agent runs on TrueForge. The core is a set of deterministic MCP tools written in Python. It pulls the flag inventory from Unleash, traces every reference with ripgrep down to file and line, classifies with an ordered rule set, generates the removal patch, runs the test suite, and only then opens a pull request.

The TrueForge agent follows a git backed skill that pins the exact procedure, so it cannot freestyle. When it wants to open a PR, TrueForge pauses and asks for my approval in chat. The GitHub token I gave it has no merge permissions at all. It physically cannot merge.

For the demo I ran it against a checkout service with 8 flags. It marked 3 as safe to remove, confirmed 3 are still live from real traffic metrics, and said "I do not know" on 2 that are built with dynamic key names. It asked me what to do. I answered. It proceeded. Two real pull requests are open on GitHub right now.

It broke things too. While running, the TrueForge harness itself crashed when a registered MCP server went down. I isolated the crash and filed it upstream. My first open source bug report, filed during a hackathon.

The lesson so far: the interesting part of agent engineering is not the model. It is the boundaries. What the agent may do, what it must ask about, and what it can never do.

Repo: https://github.com/Ata-Ul-Hai/flag-reaper
Full writeup: SOLUTION.md in the repo

#agentsthatact #OpenSource #FeatureFlags #AIagents #SoftwareEngineering
