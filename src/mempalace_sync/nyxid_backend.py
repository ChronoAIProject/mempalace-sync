"""NyxID node integration (v0.2 — designed, not yet implemented).

This module is a STUB for v0.2. See docs/ARCHITECTURE.md Mode B for the
full architecture.

----------------------------------------------------------------------------
WHAT THIS WILL DO
----------------------------------------------------------------------------

NyxID (https://github.com/ChronoAIProject/NyxID) is the open-source Agent
Connectivity Gateway from Chrono. It provides:

- `nyxid node` for NAT traversal — exposes a localhost service to the
  NyxID cloud gateway, no port forwarding needed
- Per-agent scoped tokens
- Auto-generated MCP config for client AI tools (Claude Code, Cursor,
  Codex, etc.)

In v0.2 of mempalace-sync, this module will:

1. Detect whether `nyxid` CLI is installed locally
2. Start `nyxid node` for the mempalace-sync MCP server endpoint
3. Generate per-client MCP configs (one per device that needs access)
4. Print copy-pastable instructions for each client to add the MCP endpoint
5. Tear down the node cleanly on shutdown

----------------------------------------------------------------------------
PROPOSED CLI SURFACE
----------------------------------------------------------------------------

mempalace-sync host start [--port 8765]
    Start MemPalace MCP wrapper + nyxid node. Run on your always-on
    machine.

mempalace-sync host stop
    Tear down everything started by `host start`.

mempalace-sync host issue --client mac-laptop
    Issue a per-client token + print MCP config snippet for that device.

mempalace-sync host revoke --client mac-laptop
    Revoke a previously-issued client token.

mempalace-sync client connect <nyxid_endpoint> <token>
    Configure local Claude Code / Codex / Cursor MCP to point at the
    given NyxID endpoint with the given token. No MemPalace install
    needed locally.

----------------------------------------------------------------------------
WHY NOT BUILT YET
----------------------------------------------------------------------------

- We need a working `nyxid` CLI on the machine to test
- We need to confirm the exact `nyxid node` registration format
- We want to write this against a stable NyxID API rather than its
  current beta

Until then, fall back to the v0.1 git mode.
"""

from __future__ import annotations


def is_available() -> bool:
    """Return True if `nyxid` CLI is on PATH. NOT YET WIRED."""

    return False


def start_node(local_port: int) -> None:
    """Start `nyxid node` exposing local_port. NOT YET IMPLEMENTED."""

    raise NotImplementedError(
        "NyxID backend is v0.2. See docs/ARCHITECTURE.md Mode B for the design."
    )


def issue_client_token(client_label: str) -> dict:
    """Issue a scoped client token. NOT YET IMPLEMENTED."""

    raise NotImplementedError(
        "NyxID backend is v0.2. See docs/ARCHITECTURE.md Mode B for the design."
    )
