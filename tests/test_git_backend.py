"""Tests for git_backend.py against a real local git repo."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from mempalace_sync.git_backend import (
    GitError,
    init,
    is_git_repo,
    pull,
    push,
    status,
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)


@pytest.fixture
def remote_repo(tmp_path: Path) -> Path:
    """Create a bare repo to act as a fake origin."""

    bare = tmp_path / "remote.git"
    bare.mkdir()
    subprocess.run(["git", "init", "--bare", "-b", "main"], cwd=str(bare), check=True, capture_output=True)
    return bare


@pytest.fixture
def local_repo(tmp_path: Path, remote_repo: Path) -> Path:
    """Create a working repo wired to the bare remote."""

    work = tmp_path / "palace"
    work.mkdir()
    init(work, remote_url=str(remote_repo))
    _git(work, "config", "user.email", "test@example.com")
    _git(work, "config", "user.name", "Test")
    (work / "seed.txt").write_text("hello\n", encoding="utf-8")
    _git(work, "add", "-A")
    _git(work, "commit", "-m", "seed")
    _git(work, "push", "origin", "main")
    return work


def test_init_creates_repo(tmp_path: Path) -> None:
    target = tmp_path / "fresh"
    init(target)
    assert is_git_repo(target)


def test_init_idempotent(tmp_path: Path, remote_repo: Path) -> None:
    target = tmp_path / "twice"
    init(target, remote_url=str(remote_repo))
    init(target, remote_url=str(remote_repo))
    assert is_git_repo(target)


def test_status_clean(local_repo: Path) -> None:
    snap = status(local_repo)
    assert snap.is_repo
    assert snap.has_remote
    assert snap.branch == "main"
    assert snap.ahead == 0
    assert snap.behind == 0
    assert not snap.dirty


def test_status_dirty(local_repo: Path) -> None:
    (local_repo / "new.txt").write_text("new\n", encoding="utf-8")
    snap = status(local_repo)
    assert snap.dirty


def test_push_commits_changes(local_repo: Path) -> None:
    (local_repo / "added.txt").write_text("hi\n", encoding="utf-8")
    _git(local_repo, "config", "user.email", "test@example.com")
    _git(local_repo, "config", "user.name", "Test")
    result = push(local_repo, message="add file")
    assert "pushed" in result
    snap = status(local_repo)
    assert not snap.dirty


def test_push_nothing_to_commit(local_repo: Path) -> None:
    result = push(local_repo)
    assert "nothing to commit" in result


def test_pull_no_remote_raises(tmp_path: Path) -> None:
    target = tmp_path / "noremote"
    init(target)
    with pytest.raises(GitError) as exc_info:
        pull(target)
    assert "no git remote" in str(exc_info.value)


def test_status_not_a_repo(tmp_path: Path) -> None:
    snap = status(tmp_path / "missing")
    assert not snap.is_repo
    assert not snap.has_remote
