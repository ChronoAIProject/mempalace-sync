"""Persistent configuration for mempalace-sync."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path.home() / ".config" / "mempalace-sync"
CONFIG_PATH = CONFIG_DIR / "config.yaml"


@dataclass(slots=True)
class Config:
    """User configuration for mempalace-sync.

    Stored at ~/.config/mempalace-sync/config.yaml as plain YAML so users
    can edit it by hand without running CLI commands.
    """

    remote_url: str | None = None
    data_dir: str | None = None
    backend: str = "git"
    auto_pull_on_session_start: bool = True

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        """Load config from disk. Returns defaults if file does not exist."""

        if not path.exists():
            return cls()
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise RuntimeError(
                "Failed to parse " + str(path) + ": " + str(exc) + "\n"
                "Either fix the YAML by hand or delete the file to reset."
            ) from exc
        if not isinstance(data, dict):
            raise RuntimeError(
                "Config at " + str(path) + " is not a YAML mapping. "
                "Delete the file to reset."
            )
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def save(self, path: Path = CONFIG_PATH) -> None:
        """Persist the config to disk, creating parent dirs as needed."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(asdict(self), allow_unicode=True, sort_keys=True),
            encoding="utf-8",
        )

    def get(self, key: str) -> Any:
        """Read a single field by name."""

        if key not in self.__dataclass_fields__:
            raise KeyError("Unknown config key: " + key)
        return getattr(self, key)

    def set(self, key: str, value: Any) -> None:
        """Set a single field by name with type coercion for known fields."""

        if key not in self.__dataclass_fields__:
            raise KeyError(
                "Unknown config key: " + key + ". Known keys: "
                + ", ".join(sorted(self.__dataclass_fields__))
            )
        if key == "auto_pull_on_session_start":
            value = str(value).lower() in {"1", "true", "yes", "on"}
        setattr(self, key, value)
