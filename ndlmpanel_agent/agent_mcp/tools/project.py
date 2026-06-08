"""Git and project workflow tools for coding agents."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .command import getCommandHistory, runCommand


def getGitStatus(cwd: str = ".") -> dict[str, Any]:
    """Return structured git branch and working tree status."""
    workdir = Path(cwd).expanduser().resolve()
    inside = _git(workdir, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {"success": True, "cwd": str(workdir), "isRepository": False}

    branch = _git(workdir, ["branch", "--show-current"]).stdout.strip()
    head = _git(workdir, ["rev-parse", "--short", "HEAD"]).stdout.strip()
    root = _git(workdir, ["rev-parse", "--show-toplevel"]).stdout.strip()
    porcelain = _git(workdir, ["status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines()
    changed = [_parseStatusLine(line) for line in porcelain]
    return {
        "success": True,
        "cwd": str(workdir),
        "isRepository": True,
        "root": root,
        "branch": branch,
        "head": head,
        "dirty": bool(changed),
        "changedFiles": changed,
    }


def getGitDiff(
    cwd: str = ".",
    path: str | None = None,
    staged: bool = False,
    maxBytes: int = 65536,
) -> dict[str, Any]:
    """Return git diff text with byte truncation metadata."""
    workdir = Path(cwd).expanduser().resolve()
    command = ["diff"]
    if staged:
        command.append("--cached")
    if path:
        command.extend(["--", path])
    result = _git(workdir, command, timeout=15)
    limit = max(1, int(maxBytes))
    raw = result.stdout.encode("utf-8", errors="replace")
    truncated = len(raw) > limit
    if truncated:
        raw = raw[:limit]
    return {
        "success": result.returncode == 0,
        "cwd": str(workdir),
        "path": path,
        "staged": staged,
        "returnCode": result.returncode,
        "diff": raw.decode("utf-8", errors="replace"),
        "diffBytes": len(result.stdout.encode("utf-8", errors="replace")),
        "diffReturnedBytes": len(raw),
        "truncated": truncated,
        "stderr": result.stderr,
    }


def listGitChangedFiles(cwd: str = ".") -> dict[str, Any]:
    """Return changed git files only."""
    status = getGitStatus(cwd)
    if not status.get("isRepository"):
        return {**status, "changedFiles": []}
    return {
        "success": True,
        "cwd": status["cwd"],
        "isRepository": True,
        "changedFiles": status["changedFiles"],
        "total": len(status["changedFiles"]),
    }


def detectProjectCommands(cwd: str = ".") -> dict[str, Any]:
    """Detect likely test, lint, and build commands from project files."""
    workdir = Path(cwd).expanduser().resolve()
    commands: dict[str, list[list[str]]] = {"test": [], "lint": [], "build": []}
    markers = []

    if (workdir / "pyproject.toml").exists() or (workdir / "requirements.txt").exists() or (workdir / "setup.py").exists():
        markers.append("python")
        if (workdir / "tests").exists():
            commands["test"].append(["python", "-m", "unittest", "discover", "-s", "tests"])
        commands["test"].append(["python", "-m", "pytest"])
        commands["lint"].append(["python", "-m", "ruff", "check", "."])

    package_json = workdir / "package.json"
    if package_json.exists():
        markers.append("node")
        scripts = _packageScripts(package_json)
        for kind in ("test", "lint", "build"):
            if kind in scripts:
                commands[kind].append(["npm", "run", kind])

    if (workdir / "go.mod").exists():
        markers.append("go")
        commands["test"].append(["go", "test", "./..."])
        commands["build"].append(["go", "build", "./..."])

    if (workdir / "Cargo.toml").exists():
        markers.append("rust")
        commands["test"].append(["cargo", "test"])
        commands["build"].append(["cargo", "build"])

    return {
        "success": True,
        "cwd": str(workdir),
        "detectedProjectTypes": markers,
        "commands": commands,
    }


def runProjectCheck(
    cwd: str = ".",
    kind: str = "test",
    command: list[str] | None = None,
    timeoutSeconds: int = 120,
    maxOutputBytes: int = 65536,
) -> dict[str, Any]:
    """Run a detected or explicit project check command."""
    normalized_kind = str(kind).strip().lower()
    if normalized_kind not in {"test", "lint", "build"}:
        raise ValueError("kind must be one of: test, lint, build")

    chosen = command
    detection = detectProjectCommands(cwd)
    if chosen is None:
        candidates = detection["commands"].get(normalized_kind) or []
        if not candidates:
            raise ValueError(f"No {normalized_kind} command detected")
        chosen = candidates[0]

    result = runCommand(
        chosen,
        cwd=cwd,
        timeoutSeconds=timeoutSeconds,
        maxOutputBytes=maxOutputBytes,
    )
    return {
        "success": result["success"] and result["returnCode"] == 0,
        "kind": normalized_kind,
        "selectedCommand": chosen,
        "returnCode": result.get("returnCode"),
        "durationMs": result.get("durationMs"),
        "timedOut": result.get("timedOut", False),
        "truncated": result.get("truncated", False),
        "detectedCommands": detection["commands"],
        "result": result,
    }


def summarizeFile(path: str, maxLines: int = 80) -> dict[str, Any]:
    """Return lightweight file metadata and leading text lines."""
    target = Path(path).expanduser().resolve()
    if not target.is_file():
        raise FileNotFoundError(str(target))
    raw = target.read_bytes()
    lines = raw.decode("utf-8", errors="replace").splitlines()
    limit = max(1, int(maxLines))
    return {
        "success": True,
        "path": str(target),
        "sizeBytes": len(raw),
        "totalLines": len(lines),
        "previewLines": lines[:limit],
        "truncated": len(lines) > limit,
    }


def summarizeWorkspace(path: str = ".", maxFiles: int = 200) -> dict[str, Any]:
    """Return a lightweight workspace summary."""
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(str(root))
    files = []
    for item in sorted(root.rglob("*"), key=lambda value: str(value).lower()):
        if item.is_file():
            files.append(str(item.relative_to(root)))
            if len(files) >= maxFiles:
                break
    return {
        "success": True,
        "path": str(root),
        "git": getGitStatus(str(root)),
        "projectCommands": detectProjectCommands(str(root)),
        "files": files,
        "truncated": len(files) >= maxFiles,
    }


def explainToolError(errorMessage: str, toolName: str = "") -> dict[str, Any]:
    """Classify a tool error and suggest a next action."""
    message = errorMessage or ""
    lower = message.lower()
    suggestions = []
    if "no such file" in lower or "filenotfounderror" in lower:
        suggestions.append("Check the path with listFiles or statPaths before retrying.")
    elif "oldtext was not found" in lower or "pattern did not match" in lower:
        suggestions.append("Re-read the target file and use searchText to locate the current text.")
    elif "corrupt patch" in lower or "patch does not apply" in lower:
        suggestions.append("Use replaceRange/replaceText for small edits or regenerate the unified diff.")
    elif "timed out" in lower:
        suggestions.append("Increase timeoutSeconds or run a narrower command.")
    else:
        suggestions.append("Inspect the tool arguments and retry with a smaller, more specific operation.")
    return {
        "success": True,
        "toolName": toolName,
        "errorMessage": errorMessage,
        "suggestions": suggestions,
    }


def getRecentCommandResults(limit: int = 10) -> dict[str, Any]:
    """Return recent command history if command recording is enabled."""
    results = getCommandHistory(limit)
    return {
        "success": True,
        "recordingEnabled": True,
        "scope": "current MCP process memory",
        "results": results,
        "totalReturned": len(results),
    }


def _git(cwd: Path, args: list[str], timeout: int = 10) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(["git", *args], 1, "", str(exc))


def _parseStatusLine(line: str) -> dict[str, Any]:
    status = line[:2]
    path = line[3:] if len(line) > 3 else ""
    return {
        "path": path,
        "indexStatus": status[0].strip() or "unmodified",
        "worktreeStatus": status[1].strip() or "unmodified",
        "likelyGenerated": _isLikelyGenerated(path),
        "likelyBinary": _isLikelyBinary(path),
        "raw": line,
    }


def _isLikelyGenerated(path: str) -> bool:
    normalized = path.replace("\\", "/")
    generated_markers = (
        "__pycache__/",
        ".pytest_cache/",
        "node_modules/",
        "dist/",
        "build/",
        ".ruff_cache/",
        ".mypy_cache/",
        ".venv/",
        "coverage/",
    )
    generated_suffixes = (
        ".pyc",
        ".pyo",
        ".class",
        ".o",
        ".so",
        ".dll",
        ".dylib",
        ".egg-info",
    )
    return normalized.endswith(generated_suffixes) or any(marker in normalized for marker in generated_markers)


def _isLikelyBinary(path: str) -> bool:
    binary_suffixes = (
        ".pyc",
        ".pyo",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".tgz",
        ".xz",
        ".7z",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".class",
        ".o",
    )
    return path.lower().endswith(binary_suffixes)


def _packageScripts(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = data.get("scripts")
    return scripts if isinstance(scripts, dict) else {}
