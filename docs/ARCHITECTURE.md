# Architecture

`mempalace-sync` is intentionally small. ~700 lines of Python wrapping `git`.

## The data flow

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
              │ MCP                      │ MCP
              ▼                          ▼
   ┌──────────────────────┐   ┌──────────────────────┐
   │  Claude / Codex /    │   │  Claude / Codex /    │
   │  Cursor / Gemini     │   │  Cursor / Gemini     │
   └──────────────────────┘   └──────────────────────┘
```

The trick: MemPalace exposes memory via MCP, so **any** MCP-compatible agent reads from the same directory. Sync the directory once, every agent benefits.

## Design decisions

### Why git, not S3 or rclone

Every developer already has git. Zero new dependencies. SSH keys for private repos already work. Conflict resolution is handled by git itself. We can swap to rclone in v0.2 if users complain about binary file diffs.

### Why no merge magic

ChromaDB and SQLite store binary files that don't merge cleanly. For a single user with multiple machines, **last-writer-wins** is correct 99% of the time. The other 1% is manual resolution. Trying to be clever here introduces more bugs than it solves.

### Why MemPalace data dir, not the whole `~/.mempalace`

`~/.mempalace/` may contain logs, cache, lock files, and per-machine state that should NOT sync. The `palace/` subdirectory is the actual data. We sync only that.

### Why a Claude Code SessionStart hook

Most users forget to pull. The hook makes pull-on-start automatic so a fresh terminal on a fresh machine always has the latest memory before any agent reads from MemPalace.

### Why subprocess git, not GitPython

GitPython adds binary deps, slower install, and we only use 5 commands (init, fetch, pull, commit, push). Subprocess is cleaner and works on every machine that has git already.

### What's NOT in v0.1

- Web UI
- Multi-user team merge resolution
- Automated cron schedules (the hook is enough for now)
- Remote backends other than git
- Encryption (use SSH + private repo for now)
- Selective sync (rules about which files to skip)

These are real ideas. They live in `ROADMAP.md` after the project finds users.

## File map

```
mempalace-sync/
├── README.md
├── LICENSE
├── pyproject.toml
├── src/mempalace_sync/
│   ├── __init__.py        # __version__
│   ├── paths.py           # Resolve MemPalace data dir
│   ├── config.py          # ~/.config/mempalace-sync/config.yaml
│   ├── git_backend.py     # subprocess git wrapper, GitStatus, GitError
│   ├── hook.py            # Claude Code SessionStart hook install/uninstall
│   └── cli.py             # Click CLI: init, pull, push, status, hook, config
├── claude-skill/.claude/skills/memsync/
│   └── SKILL.md           # Claude Code skill definition
├── scripts/
│   └── install-skill.sh   # Copy skill into ~/.claude/skills/memsync/
├── tests/
│   ├── test_paths.py      # Resolution rules
│   └── test_git_backend.py # Real-git integration tests
└── docs/
    └── ARCHITECTURE.md    # This file
```
