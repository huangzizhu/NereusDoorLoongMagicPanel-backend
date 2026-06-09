"""Workspace inspection tools for coding agents."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


def getWorkspaceContext(path: str = ".") -> dict[str, Any]:
    """Return workspace cwd, Python runtime, git summary, and top-level project files."""
    cwd = Path(path).expanduser().resolve()
    if not cwd.exists():
        raise FileNotFoundError(str(cwd))
    if cwd.is_file():
        cwd = cwd.parent
    return {
        "success": True,
        "cwd": str(cwd),
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "git": _gitSummary(cwd),
        "projectFiles": _projectFiles(cwd),
        "detectedProjectTypes": _detectProjectTypes(cwd),
    }


def _gitSummary(cwd: Path) -> dict[str, Any]:
    inside = _runGit(cwd, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {"isRepository": False}

    root = _runGit(cwd, ["rev-parse", "--show-toplevel"]).stdout.strip()
    branch = _runGit(cwd, ["branch", "--show-current"]).stdout.strip()
    head = _runGit(cwd, ["rev-parse", "--short", "HEAD"]).stdout.strip()
    status = _runGit(cwd, ["status", "--short"]).stdout.splitlines()
    return {
        "isRepository": True,
        "root": root,
        "branch": branch,
        "head": head,
        "dirty": bool(status),
        "statusCount": len(status),
        "statusPreview": status[:50],
    }


def _projectFiles(cwd: Path) -> dict[str, Any]:
    markers = (
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "package.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "Cargo.toml",
        "go.mod",
        "README.md",
    )
    found = [name for name in markers if (cwd / name).exists()]
    entries = []
    for child in sorted(cwd.iterdir(), key=lambda item: item.name.lower())[:100]:
        entries.append(
            {
                "path": child.name,
                "type": "directory" if child.is_dir() else "file",
            }
        )
    return {"markers": found, "topLevelEntries": entries}


def _detectProjectTypes(cwd: Path) -> list[str]:
    types = []
    markers = {
        "python": ("pyproject.toml", "requirements.txt", "setup.py"),
        "node": ("package.json",),
        "rust": ("Cargo.toml",),
        "go": ("go.mod",),
    }
    for project_type, names in markers.items():
        if any((cwd / name).exists() for name in names):
            types.append(project_type)
    return types


def _runGit(cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return subprocess.CompletedProcess(["git", *args], 1, "", "")
