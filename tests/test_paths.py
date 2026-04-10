"""Tests for paths.py override behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from mempalace_sync.paths import DEFAULT_DATA_DIR, ENV_VAR, ensure_exists, get_data_dir


def test_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)
    assert get_data_dir() == DEFAULT_DATA_DIR.expanduser().resolve()


def test_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ENV_VAR, str(tmp_path))
    assert get_data_dir() == tmp_path.resolve()


def test_explicit_override_beats_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv(ENV_VAR, str(tmp_path))
    assert get_data_dir(other) == other.resolve()


def test_ensure_exists_passes(tmp_path: Path) -> None:
    ensure_exists(tmp_path)


def test_ensure_exists_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError) as exc_info:
        ensure_exists(missing)
    msg = str(exc_info.value)
    assert "MemPalace data directory not found" in msg
    assert "pip install mempalace" in msg
