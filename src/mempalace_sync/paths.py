"""Resolve the MemPalace data directory across machines."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".mempalace" / "palace"
ENV_VAR = "MEMPALACE_DATA_DIR"


def get_data_dir(override: str | Path | None = None) -> Path:
    """Return the resolved MemPalace data directory.

    Resolution order:
      1. Explicit override (CLI flag)
      2. MEMPALACE_DATA_DIR environment variable
      3. Default ~/.mempalace/palace

    Returns a fully resolved Path. Does not check existence — use
    ensure_exists() for that.
    """

    if override is not None:
        return Path(override).expanduser().resolve()
    env_value = os.environ.get(ENV_VAR)
    if env_value:
        return Path(env_value).expanduser().resolve()
    return DEFAULT_DATA_DIR.expanduser().resolve()


def ensure_exists(data_dir: Path) -> None:
    """Raise a helpful error if the MemPalace data directory is missing.

    The error message tells the user how to fix the situation rather than
    just reporting failure.
    """

    if data_dir.exists() and data_dir.is_dir():
        return
    raise FileNotFoundError(
        "MemPalace data directory not found at: " + str(data_dir) + "\n"
        "\n"
        "Possible fixes:\n"
        "  1. Install MemPalace first:  pip install mempalace\n"
        "  2. Initialize it:            mempalace init <your project dir>\n"
        "  3. If your data lives elsewhere, point us at it:\n"
        "       mempalace-sync --data-dir /path/to/palace ...\n"
        "       or set MEMPALACE_DATA_DIR=/path/to/palace\n"
        "\n"
        "We never modify MemPalace data directly, we only wrap it in git."
    )
