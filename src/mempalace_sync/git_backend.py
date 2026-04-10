"""Subprocess-based git backend.

We deliberately avoid GitPython so the package has zero binary dependencies
and works on every machine that already has the git CLI.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    """Raised when a git command fails. The message tells the user what to do."""


@dataclass(slots=True)
class GitStatus:
    """Snapshot of a working directory's git state."""

    is_repo: bool
    has_remote: bool
    branch: str | None
    ahead: int
    behind: int
    dirty: bool
    summary: str


def _run(repo_dir: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command inside repo_dir and return the completed process."""

    result = subprocess.run(
        ["git", *args],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise GitError(
            "git " + " ".join(args) + " failed in " + str(repo_dir) + "\n"
            "stdout: " + (result.stdout.strip() or "(empty)") + "\n"
            "stderr: " + (result.stderr.strip() or "(empty)")
        )
    return result


def is_git_repo(repo_dir: Path) -> bool:
    """Return True if repo_dir contains a git working tree."""

    if not repo_dir.exists():
        return False
    result = _run(repo_dir, ["rev-parse", "--is-inside-work-tree"], check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"


def init(repo_dir: Path, remote_url: str | None = None, default_branch: str = "main") -> None:
    """Initialize a git repo at repo_dir, optionally setting a remote.

    Idempotent: skips init if already a repo, skips remote add if remote
    already configured.
    """

    repo_dir.mkdir(parents=True, exist_ok=True)
    if not is_git_repo(repo_dir):
        _run(repo_dir, ["init", "-b", default_branch])
    if remote_url:
        existing = _run(repo_dir, ["remote", "get-url", "origin"], check=False)
        if existing.returncode == 0:
            current = existing.stdout.strip()
            if current != remote_url:
                _run(repo_dir, ["remote", "set-url", "origin", remote_url])
        else:
            _run(repo_dir, ["remote", "add", "origin", remote_url])


def status(repo_dir: Path) -> GitStatus:
    """Return a structured GitStatus for repo_dir.

    Never raises on missing repo or missing remote — returns a status object
    that callers can inspect.
    """

    if not is_git_repo(repo_dir):
        return GitStatus(
            is_repo=False, has_remote=False, branch=None,
            ahead=0, behind=0, dirty=False,
            summary="not a git repo: " + str(repo_dir),
        )

    branch_result = _run(repo_dir, ["branch", "--show-current"], check=False)
    branch = branch_result.stdout.strip() or None

    remote_result = _run(repo_dir, ["remote"], check=False)
    has_remote = bool(remote_result.stdout.strip())

    dirty_result = _run(repo_dir, ["status", "--porcelain"], check=False)
    dirty = bool(dirty_result.stdout.strip())

    ahead = 0
    behind = 0
    if has_remote and branch:
        rev_result = _run(
            repo_dir,
            ["rev-list", "--left-right", "--count", "origin/" + branch + "..." + branch],
            check=False,
        )
        if rev_result.returncode == 0 and rev_result.stdout.strip():
            parts = rev_result.stdout.strip().split()
            if len(parts) == 2:
                behind = int(parts[0])
                ahead = int(parts[1])

    summary_parts = []
    if branch:
        summary_parts.append("branch=" + branch)
    summary_parts.append("ahead=" + str(ahead))
    summary_parts.append("behind=" + str(behind))
    summary_parts.append("dirty=" + ("yes" if dirty else "no"))
    summary_parts.append("remote=" + ("yes" if has_remote else "no"))

    return GitStatus(
        is_repo=True, has_remote=has_remote, branch=branch,
        ahead=ahead, behind=behind, dirty=dirty,
        summary=" ".join(summary_parts),
    )


def pull(repo_dir: Path) -> str:
    """Fetch + rebase from origin. Returns a one-line summary."""

    snap = status(repo_dir)
    if not snap.is_repo:
        raise GitError("not a git repo: " + str(repo_dir) + " — run `mempalace-sync init` first")
    if not snap.has_remote:
        raise GitError(
            "no git remote configured for " + str(repo_dir) + "\n"
            "Add one with: mempalace-sync init --remote <git_url>"
        )
    branch = snap.branch or "main"
    fetch = _run(repo_dir, ["fetch", "origin", branch], check=False)
    if fetch.returncode != 0:
        raise GitError(
            "git fetch failed for branch " + branch + ":\n"
            + (fetch.stderr.strip() or "no stderr")
            + "\n\nCheck your network and that the remote branch exists."
        )
    rebase = _run(repo_dir, ["pull", "--rebase", "origin", branch], check=False)
    if rebase.returncode != 0:
        raise GitError(
            "git pull --rebase failed. Likely a merge conflict.\n"
            "Resolve manually in " + str(repo_dir) + " then re-run pull.\n\n"
            + (rebase.stderr.strip() or "")
        )
    return "pulled origin/" + branch + " into " + str(repo_dir)


def push(repo_dir: Path, message: str | None = None) -> str:
    """Add + commit + push everything in repo_dir. Skips commit if clean."""

    snap = status(repo_dir)
    if not snap.is_repo:
        raise GitError("not a git repo: " + str(repo_dir))
    if not snap.has_remote:
        raise GitError(
            "no git remote configured for " + str(repo_dir) + "\n"
            "Add one with: mempalace-sync init --remote <git_url>"
        )

    _run(repo_dir, ["add", "-A"])
    diff_check = _run(repo_dir, ["diff", "--cached", "--quiet"], check=False)
    nothing_to_commit = diff_check.returncode == 0

    if not nothing_to_commit:
        commit_message = message or "sync from mempalace-sync"
        _run(repo_dir, ["commit", "-m", commit_message])

    branch = snap.branch or "main"
    push_result = _run(repo_dir, ["push", "origin", branch], check=False)
    if push_result.returncode != 0:
        raise GitError(
            "git push failed:\n"
            + (push_result.stderr.strip() or "no stderr") + "\n\n"
            "Try `mempalace-sync pull` first to merge remote changes."
        )

    if nothing_to_commit:
        return "nothing to commit, pushed existing branch " + branch
    return "committed and pushed branch " + branch
