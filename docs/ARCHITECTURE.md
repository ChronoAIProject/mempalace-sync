# Architecture

`mempalace-sync` ships with **two operating modes** that solve the same problem at different complexity levels.

## The problem

[MemPalace](https://github.com/milla-jovovich/mempalace) stores AI memory locally in `~/.mempalace/palace/` (ChromaDB + SQLite + filesystem). It exposes this via MCP so any agent (Claude Code, Codex, Cursor, Gemini CLI) can read from it.

But it's local-only. Multiple machines = multiple disconnected memories.

## Two solutions

| | **Mode A: Git Sync** | **Mode B: NyxID Gateway** |
|---|---|---|
| **Status** | v0.1 — shipped | v0.2 — designed, in progress |
| **Architecture** | Each machine has a full copy, synced via git | One host, many remote clients via NyxID tunnel |
| **Source of truth** | Last writer wins | Single host instance |
| **Real-time** | No (push/pull manually or via hook) | Yes (writes are immediately visible) |
| **Client install** | MemPalace + mempalace-sync + git remote | Just NyxID MCP config — no local MemPalace |
| **Conflict handling** | git merge (binary files = pain) | Doesn't exist — single writer |
| **Setup complexity** | 5 minutes | 15-30 minutes (NyxID node + token + tunnel) |
| **Best for** | Solo dev, occasional machine switches | Always-on home machine + multi-device daily use, or team |
| **Network requirement** | Just git access | Always-online host + NyxID gateway access |

You can run both. Mode A is the fallback when the host is offline.

---

## Mode A: Git Sync (v0.1)

```
                ┌─────────────────────────┐
                │  Private git remote     │
                │  (GitHub / GitLab / SSH)│
                └────────────┬────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        git push│                         │git pull
                │                         │
                ▼                         ▼
   ┌──────────────────────┐   ┌──────────────────────┐
   │  Mac (~/.mempalace)  │   │  Linux (~/.mempalace)│
   │                      │   │                      │
   │  MemPalace ChromaDB  │   │  MemPalace ChromaDB  │
   │  + SQLite            │   │  + SQLite            │
   │  + filesystem        │   │  + filesystem        │
   └──────────┬───────────┘   └──────────┬───────────┘
              │                          │
              │ MCP (local)              │ MCP (local)
              ▼                          ▼
   ┌──────────────────────┐   ┌──────────────────────┐
   │  Claude / Codex /    │   │  Claude / Codex /    │
   │  Cursor / Gemini     │   │  Cursor / Gemini     │
   └──────────────────────┘   └──────────────────────┘
```

**How it works**:
1. The MemPalace data dir is wrapped in a git repo
2. `mempalace-sync push` commits and pushes
3. `mempalace-sync pull` rebases from remote
4. A Claude Code SessionStart hook can auto-pull
5. Each machine reads MemPalace locally — agents are unaware of sync

**Trade-offs**:
- ✅ Simple, reliable, offline-friendly
- ✅ No always-on infrastructure required
- ❌ Manual sync discipline needed
- ❌ ChromaDB binary files don't merge well — last writer wins
- ❌ Clients must install MemPalace + Python

---

## Mode B: NyxID Gateway (v0.2 — designed)

This is the architecture [Auric (Chrono CEO)](https://github.com/loning) suggested. It treats MemPalace as a service rather than a synced file tree.

```
                    ┌──────────────── Memory Host (e.g. 4060) ────────────────┐
                    │                                                          │
                    │   MemPalace (localhost:8765)                            │
                    │        ↑                                                 │
                    │   mempalace-sync (host mode)                            │
                    │        - thin REST/MCP wrapper                           │
                    │        - exposes /memory/search /memory/status etc.     │
                    │        ↑                                                 │
                    │   nyxid node                                             │
                    │        - NAT traversal                                   │
                    │        - per-agent token issuance                        │
                    │        ↓                                                 │
                    └────────┼────────────────────────────────────────────────┘
                             │
                             │ encrypted tunnel
                             ▼
                    ┌──────────────────────────────────┐
                    │  NyxID Cloud Gateway             │
                    │  - per-agent scoped tokens       │
                    │  - MCP routing                   │
                    │  - revocable sessions            │
                    └──────────┬─────────────┬─────────┘
                               │             │
                               │             │
              ┌────────────────┘             └────────────────┐
              │                                                │
              ▼                                                ▼
   ┌──────────────────────┐                       ┌──────────────────────┐
   │  Mac (client)        │                       │  Linux (client)      │
   │                      │                       │                      │
   │  Claude Code         │                       │  Codex / Cursor      │
   │  └─ MCP config       │                       │  └─ MCP config       │
   │     points at NyxID  │                       │     points at NyxID  │
   │                      │                       │                      │
   │  No MemPalace        │                       │  No MemPalace        │
   │  No local data       │                       │  No local data       │
   └──────────────────────┘                       └──────────────────────┘
```

**How it works**:
1. **One machine** (your always-on host — laptop, 4060, NAS, whatever) runs MemPalace + mempalace-sync in `host` mode
2. **`nyxid node`** runs on the same machine and exposes mempalace-sync's MCP endpoint to the NyxID cloud gateway
3. **Other machines** configure their AI clients (Claude Code / Codex / Cursor / Gemini) to use the NyxID-issued MCP endpoint
4. Every agent on every machine sees the SAME memory in real-time
5. NyxID gives each agent its own scoped token — you can revoke any device without affecting the others

**Trade-offs**:
- ✅ Single source of truth (no conflicts ever)
- ✅ Real-time updates across all machines
- ✅ Clients don't install MemPalace at all
- ✅ Per-agent isolation and revocation built-in
- ✅ Works for teams (multiple humans sharing one memory pool, with access control)
- ❌ Requires an always-on host (or accept memory is offline when host sleeps)
- ❌ More setup steps (NyxID node + tunnel + per-client MCP config)

### Why NyxID specifically

[NyxID](https://github.com/ChronoAIProject/NyxID) is Chrono's open-source Agent Connectivity Gateway. It already solves:

| Problem | NyxID's solution |
|---------|------------------|
| Make a localhost service reachable from another network | `nyxid node` (NAT traversal, no port forwarding) |
| Don't expose raw credentials to agents | Reverse proxy with credential injection |
| Wrap a REST API as MCP tools | `nyxid mcp config --tool cursor` |
| Per-agent access scoping and revocation | Built-in OIDC + scoped tokens |

mempalace-sync host mode is a perfect use case — it's a localhost service (the MemPalace MCP wrapper) that needs to be reachable from other machines, without burning real credentials and without the user setting up Cloudflare tunnels.

### Why this beats "just use Cloudflare Tunnel + bare MemPalace"

| Concern | Cloudflare Tunnel | NyxID |
|---------|-------------------|-------|
| NAT traversal | ✅ | ✅ |
| Per-agent token isolation | ❌ | ✅ |
| Auto MCP config generation | ❌ | ✅ |
| Open source | ❌ | ✅ |
| Built for AI agents specifically | ❌ | ✅ |

---

## Component map

```
mempalace-sync/
├── README.md
├── LICENSE
├── pyproject.toml
├── src/mempalace_sync/
│   ├── __init__.py             # __version__
│   ├── paths.py                # Resolve MemPalace data dir
│   ├── config.py               # ~/.config/mempalace-sync/config.yaml
│   ├── git_backend.py          # [Mode A] subprocess git wrapper
│   ├── hook.py                 # [Mode A] Claude Code SessionStart hook
│   ├── cli.py                  # CLI: init, pull, push, status, hook, config (and v0.2: host, client)
│   ├── mcp_server.py           # [Mode B - stub] MCP server for host mode
│   └── nyxid_backend.py        # [Mode B - stub] NyxID node integration
├── claude-skill/.claude/skills/memsync/
│   └── SKILL.md                # Claude Code skill definition
├── scripts/
│   └── install-skill.sh        # Copy skill into ~/.claude/skills/memsync/
├── tests/
│   ├── test_paths.py           # Resolution rules
│   └── test_git_backend.py     # Real-git integration tests (8 cases)
└── docs/
    └── ARCHITECTURE.md         # This file
```

## Roadmap

| Version | Theme | Status |
|---------|-------|--------|
| **v0.1** | Mode A — git sync, CLI, hook, tests, docs | ✅ Shipped |
| **v0.2** | Mode B — NyxID + MCP server, host mode, client mode, setup wizard | 🟡 Designed, stubs in tree |
| **v0.3** | Hybrid mode (git fallback when host offline), conflict-resolution helpers | 📋 Planned |
| **v0.4** | Selective sync rules, encryption-at-rest options, team RBAC | 📋 Planned |

## Acknowledgments

- The Mode B / NyxID architecture is **Auric Lo (Chrono AI CEO)'s suggestion**. It turns mempalace-sync from a backup tool into a multi-agent memory server. Credit where it's due.
- [MemPalace](https://github.com/milla-jovovich/mempalace) by Milla Jovovich and Ben Sigman — the memory system this tool extends.
- [NyxID](https://github.com/ChronoAIProject/NyxID) by Chrono AI — the agent connectivity gateway Mode B sits on top of.
