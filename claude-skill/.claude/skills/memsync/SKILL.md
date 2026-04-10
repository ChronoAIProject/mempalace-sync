---
name: memsync
description: Sync MemPalace AI memory across machines via git. Use when the user wants to push/pull memory, check sync status, set up sync on a new machine, or switch between Mac/Linux/Windows working environments.
---

# memsync — Cross-machine MemPalace sync

This skill wraps the `mempalace-sync` CLI so Claude Code can sync the user's MemPalace memory directory across machines automatically.

## When to use

- User says "sync my memory"
- User says "I'm switching to my other machine"
- User says "did I push my latest mining"
- User asks "what's my mempalace status"
- User just installed MemPalace on a new machine and wants their existing data
- Session start (auto-pull) — only if `mempalace-sync hook install` has been run

## Prerequisites

- `pip install mempalace-sync` (or `pipx install mempalace-sync`)
- A private git remote (GitHub, GitLab, Gitea — anything with SSH access)
- MemPalace itself installed at `~/.mempalace/palace/` (or a custom path via `MEMPALACE_DATA_DIR`)

## First-time setup on a new machine

```bash
# 1. Install mempalace-sync
pip install mempalace-sync

# 2. Initialize and pull existing memory from your private remote
mempalace-sync init --remote git@github.com:yourname/your-mempalace.git --pull

# 3. (Optional) Auto-pull on every Claude Code session start
mempalace-sync hook install
```

## Daily commands

```bash
mempalace-sync status         # See ahead/behind/dirty
mempalace-sync pull           # Get latest memory from remote
mempalace-sync push           # Commit and push local changes
mempalace-sync push -m "msg"  # With a custom commit message
```

## Multi-agent angle

Because MemPalace exposes memory via MCP, **any** MCP-compatible AI client reading from the same `~/.mempalace/palace/` directory automatically benefits from the synced data:

- Claude Code
- Codex CLI
- Cursor
- Gemini CLI
- Anything else that connects to MemPalace's MCP server

You only sync once. Every agent on every machine sees the same memory.

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| `MemPalace data directory not found` | Install MemPalace first or set `MEMPALACE_DATA_DIR=/your/path` |
| `no git remote configured` | Run `mempalace-sync init --remote <url>` first |
| `git push failed` (rejected) | Run `mempalace-sync pull` first to merge remote changes |
| `merge conflict` | Resolve manually inside `~/.mempalace/palace`, then re-run pull |
| Hook installed but not firing | Check `~/.claude/settings.json` has `hooks.SessionStart` with `mempalace-sync` tag |

## Repo

[github.com/ChronoAIProject/mempalace-sync](https://github.com/ChronoAIProject/mempalace-sync)
