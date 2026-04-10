"""Click-based CLI for mempalace-sync."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .config import CONFIG_PATH, Config
from .git_backend import GitError, init as git_init, pull as git_pull, push as git_push, status as git_status
from .hook import install_hook, uninstall_hook
from .paths import ENV_VAR, ensure_exists, get_data_dir


def _resolve_data_dir(data_dir: str | None) -> Path:
    """Resolve data dir from CLI flag, env, config, then default."""

    if data_dir:
        return get_data_dir(data_dir)
    cfg = Config.load()
    if cfg.data_dir:
        return get_data_dir(cfg.data_dir)
    return get_data_dir(None)


@click.group()
@click.version_option(__version__, prog_name="mempalace-sync")
def main() -> None:
    """Cross-machine sync for MemPalace AI memory data.

    Wraps the MemPalace data directory in git so multiple machines can
    share the same memory. Works with any MCP-compatible AI client
    (Claude Code, Codex, Cursor, Gemini CLI).
    """


@main.command()
@click.option("--remote", "remote_url", required=True, help="Git remote URL (e.g. git@github.com:you/your-mempalace.git)")
@click.option("--data-dir", default=None, help="Override MemPalace data dir (default: ~/.mempalace/palace or $" + ENV_VAR + ")")
@click.option("--pull/--no-pull", default=True, help="Pull from remote after init (default: yes)")
def init(remote_url: str, data_dir: str | None, pull: bool) -> None:
    """Initialize the MemPalace data dir as a git repo with the given remote."""

    target = _resolve_data_dir(data_dir)
    try:
        ensure_exists(target)
    except FileNotFoundError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(2)

    try:
        git_init(target, remote_url=remote_url)
    except GitError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)

    cfg = Config.load()
    cfg.remote_url = remote_url
    cfg.data_dir = str(target)
    cfg.save()
    click.secho("initialized git repo at " + str(target), fg="green")
    click.echo("remote: " + remote_url)
    click.echo("config saved to " + str(CONFIG_PATH))

    if pull:
        try:
            result = git_pull(target)
        except GitError as exc:
            click.secho("initial pull skipped: " + str(exc), fg="yellow", err=True)
            return
        click.echo(result)


@main.command()
@click.option("--data-dir", default=None, help="Override MemPalace data dir")
@click.option("--quiet", is_flag=True, help="Suppress output unless an error occurs")
def pull(data_dir: str | None, quiet: bool) -> None:
    """Pull latest memory from the remote into the local MemPalace dir."""

    target = _resolve_data_dir(data_dir)
    try:
        ensure_exists(target)
        result = git_pull(target)
    except (FileNotFoundError, GitError) as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)
    if not quiet:
        click.secho(result, fg="green")


@main.command()
@click.option("--data-dir", default=None, help="Override MemPalace data dir")
@click.option("-m", "--message", default=None, help="Commit message override")
def push(data_dir: str | None, message: str | None) -> None:
    """Commit and push local memory changes to the remote."""

    target = _resolve_data_dir(data_dir)
    try:
        ensure_exists(target)
        result = git_push(target, message=message)
    except (FileNotFoundError, GitError) as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)
    click.secho(result, fg="green")


@main.command()
@click.option("--data-dir", default=None, help="Override MemPalace data dir")
def status(data_dir: str | None) -> None:
    """Show local vs remote sync status."""

    target = _resolve_data_dir(data_dir)
    try:
        ensure_exists(target)
    except FileNotFoundError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(2)
    snap = git_status(target)
    click.echo("data_dir: " + str(target))
    click.echo("status:   " + snap.summary)
    if snap.is_repo and snap.has_remote and (snap.ahead or snap.behind):
        if snap.behind:
            click.secho("  remote has " + str(snap.behind) + " new commits — run `mempalace-sync pull`", fg="yellow")
        if snap.ahead:
            click.secho("  you have " + str(snap.ahead) + " unpushed commits — run `mempalace-sync push`", fg="yellow")


@main.group()
def hook() -> None:
    """Manage Claude Code SessionStart hook for auto-pull."""


@hook.command("install")
def hook_install() -> None:
    """Install a SessionStart hook so each Claude Code session auto-pulls."""

    try:
        result = install_hook()
    except RuntimeError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)
    click.secho(result, fg="green")


@hook.command("uninstall")
def hook_uninstall() -> None:
    """Remove the SessionStart hook from Claude Code settings."""

    try:
        result = uninstall_hook()
    except RuntimeError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(1)
    click.echo(result)


@main.group()
def config() -> None:
    """Show or edit ~/.config/mempalace-sync/config.yaml."""


@config.command("show")
def config_show() -> None:
    """Print the current config."""

    cfg = Config.load()
    click.echo("path: " + str(CONFIG_PATH))
    click.echo("remote_url:                " + (cfg.remote_url or "(unset)"))
    click.echo("data_dir:                  " + (cfg.data_dir or "(default: ~/.mempalace/palace)"))
    click.echo("backend:                   " + cfg.backend)
    click.echo("auto_pull_on_session_start: " + str(cfg.auto_pull_on_session_start))


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a config field. Example: mempalace-sync config set remote_url git@..."""

    cfg = Config.load()
    try:
        cfg.set(key, value)
    except KeyError as exc:
        click.secho(str(exc), fg="red", err=True)
        sys.exit(2)
    cfg.save()
    click.secho("saved " + key + " = " + str(cfg.get(key)), fg="green")


if __name__ == "__main__":
    main()
