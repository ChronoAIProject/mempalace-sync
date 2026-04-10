"""MCP server for host mode (v0.2 — designed, not yet implemented).

This module is a STUB for the v0.2 NyxID-based architecture proposed by
Auric (Chrono CEO). It is intentionally not implemented yet because the
exact integration patterns with NyxID node + MemPalace MCP need to be
verified against a real NyxID deployment first.

See docs/ARCHITECTURE.md (Mode B section) for the full design.

----------------------------------------------------------------------------
DESIGN OVERVIEW
----------------------------------------------------------------------------

In v0.2 host mode, mempalace-sync runs an MCP server that:

1. Wraps a local MemPalace instance (which already exposes its own MCP
   server). We do NOT replace MemPalace — we sit beside it and add
   sync-aware operations on top.

2. Exposes additional tools that bare MemPalace does not provide:

     mempalace_sync_status     — host status, # connected clients, last write
     mempalace_sync_health     — is the underlying MemPalace responsive
     mempalace_sync_locks      — see active write locks (for future
                                 multi-writer scenarios)
     mempalace_sync_audit      — recent operations log per client token

3. Forwards standard MemPalace search/store calls to the local MemPalace
   MCP server (passthrough proxy).

4. Auto-registers with a local `nyxid node` instance so the gateway can
   reach it across the network.

----------------------------------------------------------------------------
WHY NOT BUILD IT RIGHT NOW
----------------------------------------------------------------------------

- MCP protocol implementation requires either an MCP SDK or careful
  hand-rolling of JSON-RPC over stdio/HTTP. We want to use the official
  pattern, not invent our own.

- NyxID's `nyxid node` integration patterns (how exactly to register a
  service, what envelope format it expects) need to be confirmed against
  a real NyxID deployment.

- The MemPalace MCP wire format may evolve before v1.0 — building a
  passthrough proxy now risks brittleness.

We will pin this down once one of:
- A NyxID expert from Chrono walks through the integration with us
- The Anthropic MCP Python SDK stabilizes and we can build on it

----------------------------------------------------------------------------
WHAT THIS MODULE WILL EVENTUALLY EXPORT
----------------------------------------------------------------------------

class MempalaceSyncMCPServer:
    def __init__(self, mempalace_endpoint: str, nyxid_node_socket: str | None): ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def health(self) -> dict: ...

def serve(host: str, port: int, *, nyxid: bool = True) -> None:
    \"\"\"CLI entry point for `mempalace-sync host start`.\"\"\"
    raise NotImplementedError("v0.2 — see docs/ARCHITECTURE.md Mode B")
"""

from __future__ import annotations


def serve(host: str = "127.0.0.1", port: int = 8765, *, nyxid: bool = True) -> None:
    """Start the host-mode MCP server. NOT YET IMPLEMENTED.

    See module docstring and docs/ARCHITECTURE.md for the design.
    """

    raise NotImplementedError(
        "mempalace-sync host mode is v0.2 and not yet implemented. "
        "Use git mode (`mempalace-sync init/pull/push`) for now. "
        "See docs/ARCHITECTURE.md Mode B for the full design."
    )
