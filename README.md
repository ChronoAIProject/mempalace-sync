# mempalace-sync

> Cross-machine sync for [MemPalace](https://github.com/milla-jovovich/mempalace) AI memory data. Git-based, multi-agent friendly, ~700 lines of Python.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#install)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What this fixes

[MemPalace](https://github.com/milla-jovovich/mempalace) is a great local-first AI memory system. It stores everything in `~/.mempalace/palace/` (ChromaDB + SQLite + filesystem) and exposes it via MCP so any agent (Claude Code, Codex, Cursor, Gemini CLI) can read from it.

But it's **local-only**. Switch laptops, switch from Mac to Linux, hand off to a teammate — you lose every bit of context you've built up.

`mempalace-sync` is a thin wrapper that puts your MemPalace data dir under git control so it travels with you.

## How it works

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

- **v0.1** (now) — git backend, manual + hook-based sync, status command
- **v0.2** — rclone backend (S3 / Dropbox / iCloud), webhook on push
- **v0.3** — selective sync rules, conflict-resolution helpers, watch mode

## Contributing

Issues and PRs welcome at [github.com/ChronoAIProject/mempalace-sync](https://github.com/ChronoAIProject/mempalace-sync).

## Acknowledgments

- [MemPalace](https://github.com/milla-jovovich/mempalace) by Milla Jovovich and Ben Sigman — the memory system this tool wraps.
- [ChronoAIProject](https://github.com/ChronoAIProject) — the org this tool ships under.

## License

MIT. See [LICENSE](LICENSE).
