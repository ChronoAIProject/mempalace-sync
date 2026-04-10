# mempalace-sync

> Cross-machine sync for [MemPalace](https://github.com/milla-jovovich/mempalace) AI memory data. Two modes: lightweight git sync (v0.1, shipped) and a NyxID-powered multi-agent memory server (v0.2, designed).

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#install)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What this fixes

[MemPalace](https://github.com/milla-jovovich/mempalace) is a great local-first AI memory system. It stores everything in `~/.mempalace/palace/` (ChromaDB + SQLite + filesystem) and exposes it via MCP so any agent (Claude Code, Codex, Cursor, Gemini CLI) can read from it.

But it's **local-only**. Switch laptops, switch from Mac to Linux, hand off to a teammate — you lose every bit of context you've built up.

`mempalace-sync` makes your MemPalace data travel with you. We support two architectures, and you can use whichever fits your situation.

## Two modes — pick one (or both)

| | **Mode A: Git Sync (v0.1)** | **Mode B: NyxID Gateway (v0.2)** |
|---|---|---|
| Status | ✅ Shipped | 🟡 Designed, stubs in tree |
| How it works | Each machine has a copy, synced via git | One host, many remote clients via [NyxID](https://github.com/ChronoAIProject/NyxID) tunnel |
| Source of truth | Last writer wins | Single host instance — no conflicts ever |
| Real-time | No (push/pull) | Yes (writes immediately visible) |
| Client install | MemPalace + git | Just an MCP config — no MemPalace locally |
| Best for | Solo dev, occasional machine switches | Always-on home machine + multi-device daily, or team |
| Setup time | 5 minutes | 15-30 minutes |

**Don't know which to pick?** Start with Mode A. It's shipped, simple, works offline. When you have an always-on machine and want real-time multi-device, upgrade to Mode B (when v0.2 ships).

Full architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## How Mode A works (v0.1, available now)

```
            ┌──────────── private git remote ────────────┐
            │                                              │
   ┌────────┴────────┐                          ┌─────────┴────────┐
   │  Mac            │                          │  Linux (4060)    │
   │  ~/.mempalace   │ ── push ──►   ◄── pull ──│  ~/.mempalace    │
   │  Claude Code    │                          │  Claude Code     │
   │  Codex / Cursor │ ── all see same memory ──│  Codex / Cursor  │
   └─────────────────┘                          └──────────────────┘
```

You sync the directory once. Every MCP-compatible agent on every machine sees the same memory. No extra integration needed.

## Install

```bash
pip install mempalace-sync
```

(Or `pipx install mempalace-sync` for an isolated install.)

## Quick start

```bash
# 1. Create a private git repo somewhere (GitHub, GitLab, Gitea, anything with SSH)
#    e.g. github.com/yourname/your-mempalace (private!)

# 2. On your first machine
mempalace-sync init --remote git@github.com:yourname/your-mempalace.git
mempalace-sync push -m "initial sync"

# 3. On any other machine
mempalace-sync init --remote git@github.com:yourname/your-mempalace.git --pull

# 4. (Optional but recommended) Auto-pull on every Claude Code session start
mempalace-sync hook install
```

## Daily use

```bash
mempalace-sync status   # ahead / behind / dirty
mempalace-sync pull     # get latest from remote
mempalace-sync push     # commit and push local changes
```

That's it. No daemon. No background process. No cloud account.

## Multi-agent: why this is more useful than it looks

MemPalace exposes memory via MCP. Once your `~/.mempalace/palace` is in sync across machines, **every** MCP-compatible client benefits without extra config:

| Client | How it sees synced memory |
|--------|---------------------------|
| **Claude Code** | Add MemPalace MCP server, reads from local dir |
| **Codex CLI** | Same, via codex MCP config |
| **Cursor** | Same, via Cursor MCP settings |
| **Gemini CLI** | Native MemPalace integration |
| **Anything else MCP-compatible** | Read from local dir, sync handles the rest |

You sync the data once. The agents take care of the rest.

## Claude Code skill

If you use Claude Code, install the bundled skill:

```bash
git clone https://github.com/ChronoAIProject/mempalace-sync
cd mempalace-sync
./scripts/install-skill.sh
```

Then in any Claude Code session you can say:

> "sync my memory" → calls `mempalace-sync push`
> "pull latest from remote" → calls `mempalace-sync pull`
> "what's my mempalace status" → calls `mempalace-sync status`

## Design decisions

- **Git, not S3 or rclone.** Every dev has git. Zero new deps. Private repo + SSH already secure.
- **Last-writer-wins.** ChromaDB and SQLite are binary; clever merging is more bug than feature for a single-user multi-machine case.
- **Sync only `palace/`.** Not the whole `~/.mempalace/` — caches and lock files should stay local.
- **Subprocess git, no GitPython.** Pure stdlib + click + pyyaml. Faster install, fewer surprises.
- **MemPalace stays untouched.** We're a sibling tool, not a fork. Update MemPalace whenever you want.

Full details: [ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Roadmap

- **v0.1** (now) — Mode A: git backend, CLI, Claude Code SessionStart hook, 13 tests
- **v0.2** — **Mode B: NyxID gateway + MCP server.** Per Auric (Chrono CEO)'s suggestion: run MemPalace on one always-on host, expose via mempalace-sync MCP server, route through `nyxid node` so any agent on any machine connects via NyxID with per-agent scoped tokens. No more last-writer-wins, no more push/pull discipline, real-time multi-device. Stubs already in `src/mempalace_sync/mcp_server.py` and `nyxid_backend.py`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) Mode B for the full design.
- **v0.3** — Hybrid: git fallback when host is offline, conflict-resolution helpers
- **v0.4** — Team RBAC, selective sync rules, encryption-at-rest options

## Contributing

Issues and PRs welcome at [github.com/ChronoAIProject/mempalace-sync](https://github.com/ChronoAIProject/mempalace-sync).

## Acknowledgments

- **Auric Lo (Chrono AI CEO)** proposed the Mode B / NyxID architecture. It turns mempalace-sync from a backup tool into a multi-agent memory server. Credit where it's due.
- [MemPalace](https://github.com/milla-jovovich/mempalace) by Milla Jovovich and Ben Sigman — the memory system this tool extends.
- [NyxID](https://github.com/ChronoAIProject/NyxID) by Chrono AI — the agent connectivity gateway Mode B sits on top of.
- [ChronoAIProject](https://github.com/ChronoAIProject) — the org this tool ships under.

## License

MIT. See [LICENSE](LICENSE).
