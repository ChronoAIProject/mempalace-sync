"""Install / uninstall a Claude Code SessionStart hook."""

from __future__ import annotations

import json
from pathlib import Path

CLAUDE_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_KEY = "SessionStart"
HOOK_TAG = "mempalace-sync"
HOOK_COMMAND = "mempalace-sync pull --quiet"


def _load_settings(path: Path = CLAUDE_SETTINGS_PATH) -> dict:
    """Load Claude Code settings.json, returning {} if missing or empty."""

    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Failed to parse " + str(path) + ": " + str(exc) + "\n"
            "Fix the JSON by hand or back it up and let Claude Code recreate it."
        ) from exc
    if not isinstance(data, dict):
        raise RuntimeError("Claude settings root is not a JSON object")
    return data


def _save_settings(data: dict, path: Path = CLAUDE_SETTINGS_PATH) -> None:
    """Persist settings.json, creating parents if needed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _hook_entry() -> dict:
    """The single hook entry mempalace-sync owns."""

    return {
        "tag": HOOK_TAG,
        "command": HOOK_COMMAND,
        "description": "Pull latest MemPalace memory before each Claude Code session.",
    }


def install_hook(path: Path = CLAUDE_SETTINGS_PATH) -> str:
    """Install the SessionStart hook into Claude Code settings.

    Idempotent: replaces an existing entry tagged 'mempalace-sync' instead
    of duplicating it. Preserves any other hooks the user has configured.
    """

    settings = _load_settings(path)
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise RuntimeError("settings.hooks is not a JSON object — refusing to overwrite")
    bucket = hooks.setdefault(HOOK_KEY, [])
    if not isinstance(bucket, list):
        raise RuntimeError("settings.hooks." + HOOK_KEY + " is not a JSON array")

    bucket = [entry for entry in bucket if not (isinstance(entry, dict) and entry.get("tag") == HOOK_TAG)]
    bucket.append(_hook_entry())
    hooks[HOOK_KEY] = bucket
    settings["hooks"] = hooks
    _save_settings(settings, path)
    return "installed " + HOOK_KEY + " hook into " + str(path)


def uninstall_hook(path: Path = CLAUDE_SETTINGS_PATH) -> str:
    """Remove only the mempalace-sync hook entry. Leaves other hooks alone."""

    if not path.exists():
        return "no settings file at " + str(path) + " — nothing to uninstall"
    settings = _load_settings(path)
    hooks = settings.get("hooks") or {}
    if not isinstance(hooks, dict):
        return "settings.hooks not a dict — nothing to uninstall"
    bucket = hooks.get(HOOK_KEY) or []
    if not isinstance(bucket, list):
        return "settings.hooks." + HOOK_KEY + " not a list — nothing to uninstall"

    new_bucket = [entry for entry in bucket if not (isinstance(entry, dict) and entry.get("tag") == HOOK_TAG)]
    if len(new_bucket) == len(bucket):
        return "no mempalace-sync hook found to remove"

    if new_bucket:
        hooks[HOOK_KEY] = new_bucket
    else:
        hooks.pop(HOOK_KEY, None)
    if hooks:
        settings["hooks"] = hooks
    else:
        settings.pop("hooks", None)
    _save_settings(settings, path)
    return "removed mempalace-sync hook from " + str(path)
