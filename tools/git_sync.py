from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.paths import EVE_ROOT


def _run_git(args: list[str], *, cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=120,
    )
    return {
        "command": "git " + " ".join(args),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _ok(result: dict[str, Any]) -> bool:
    return int(result.get("returncode") or 0) == 0


def git_pull_updates(*, repo: str | Path | None = None, remote: str = "origin", branch: str = "main", dry_run: bool = False) -> dict[str, Any]:
    """Fetch and fast-forward the Eve repo without overwriting local work."""
    repo_path = Path(repo or EVE_ROOT).resolve()
    planned = [
        f"git fetch {remote}",
        "git rev-list --left-right --count HEAD...<upstream>",
        f"git pull --ff-only --autostash {remote} {branch}",
    ]
    if dry_run:
        return {
            "ok": True,
            "status": "dry_run",
            "repo": str(repo_path),
            "planned_commands": planned,
            "safety": "fast-forward only; autostash tracked local edits; never reset or delete files",
        }

    commands: list[dict[str, Any]] = []
    root = _run_git(["rev-parse", "--show-toplevel"], cwd=repo_path)
    commands.append(root)
    if not _ok(root):
        return {"ok": False, "status": "failed", "repo": str(repo_path), "commands": commands, "reason": "not a git repository"}

    git_root = Path(root["stdout"]).resolve()
    status_before = _run_git(["status", "--short"], cwd=git_root)
    commands.append(status_before)

    head_before = _run_git(["rev-parse", "HEAD"], cwd=git_root)
    commands.append(head_before)

    fetch = _run_git(["fetch", remote], cwd=git_root)
    commands.append(fetch)
    if not _ok(fetch):
        return {"ok": False, "status": "failed", "repo": str(git_root), "commands": commands, "reason": "git fetch failed"}

    upstream = f"{remote}/{branch}"
    counts = _run_git(["rev-list", "--left-right", "--count", f"HEAD...{upstream}"], cwd=git_root)
    commands.append(counts)
    if not _ok(counts):
        return {"ok": False, "status": "failed", "repo": str(git_root), "commands": commands, "reason": f"cannot compare with {upstream}"}

    parts = counts["stdout"].split()
    ahead = int(parts[0]) if len(parts) >= 1 and parts[0].isdigit() else 0
    behind = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0
    if behind == 0:
        return {
            "ok": True,
            "status": "up_to_date",
            "repo": str(git_root),
            "remote": remote,
            "branch": branch,
            "ahead": ahead,
            "behind": behind,
            "dirty_before": status_before["stdout"],
            "commands": commands,
        }

    pull = _run_git(["pull", "--ff-only", "--autostash", remote, branch], cwd=git_root)
    commands.append(pull)
    if not _ok(pull):
        return {
            "ok": False,
            "status": "failed",
            "repo": str(git_root),
            "remote": remote,
            "branch": branch,
            "ahead": ahead,
            "behind": behind,
            "dirty_before": status_before["stdout"],
            "commands": commands,
            "reason": "git pull --ff-only --autostash failed; manual review required before merging remote changes",
        }

    head_after = _run_git(["rev-parse", "HEAD"], cwd=git_root)
    status_after = _run_git(["status", "--short"], cwd=git_root)
    commands.extend([head_after, status_after])
    return {
        "ok": True,
        "status": "updated",
        "repo": str(git_root),
        "remote": remote,
        "branch": branch,
        "ahead_before": ahead,
        "behind_before": behind,
        "head_before": head_before["stdout"],
        "head_after": head_after["stdout"],
        "dirty_before": status_before["stdout"],
        "dirty_after": status_after["stdout"],
        "commands": commands,
    }
