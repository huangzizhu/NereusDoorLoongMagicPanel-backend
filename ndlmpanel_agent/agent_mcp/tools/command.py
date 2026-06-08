"""Command execution tool for coding agents."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any

_RECENT_COMMAND_RESULTS: list[dict[str, Any]] = []
_MAX_RECENT_COMMAND_RESULTS = 20


def runCommand(
    command: list[str],
    cwd: str = ".",
    timeoutSeconds: int = 30,
    env: dict[str, str] | None = None,
    maxOutputBytes: int = 65536,
) -> dict[str, Any]:
    """Default command tool: run argv with no shell parsing. Use for tests, builds, scripts, and simple commands; it does not support pipes, redirects, globs, variables, command substitution, or &&/|| unless you explicitly invoke a shell yourself."""
    if not command:
        raise ValueError("command must not be empty")
    if not all(isinstance(part, str) and part for part in command):
        raise ValueError("command must be a non-empty list of strings")

    return _runProcess(
        command=command,
        cwd=cwd,
        timeoutSeconds=timeoutSeconds,
        env=env,
        maxOutputBytes=maxOutputBytes,
        shell=False,
        shellCommand=None,
    )


def runShellCommand(
    command: str,
    cwd: str = ".",
    timeoutSeconds: int = 30,
    env: dict[str, str] | None = None,
    maxOutputBytes: int = 65536,
) -> dict[str, Any]:
    """Advanced shell tool: run one command string through bash -lc. Use only when shell features are required, such as pipes, redirects, globs, variables, command substitution, or &&/|| chains; prefer runCommand for normal argv-style commands."""
    if not command.strip():
        raise ValueError("command must not be empty")

    return _runProcess(
        command=["bash", "-lc", command],
        cwd=cwd,
        timeoutSeconds=timeoutSeconds,
        env=env,
        maxOutputBytes=maxOutputBytes,
        shell=False,
        shellCommand=command,
    )


def _runProcess(
    command: list[str],
    cwd: str,
    timeoutSeconds: int,
    env: dict[str, str] | None,
    maxOutputBytes: int,
    shell: bool,
    shellCommand: str | None,
) -> dict[str, Any]:
    workdir = Path(cwd).expanduser().resolve()
    timeout = max(1, int(timeoutSeconds))
    output_limit = max(1, int(maxOutputBytes))
    run_env = os.environ.copy()
    if env:
        run_env.update({str(key): str(value) for key, value in env.items()})

    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=str(workdir),
            env=run_env,
            text=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            shell=shell,
        )
        duration_ms = round((time.monotonic() - started) * 1000, 3)
        stdout, stdout_meta = _decodeAndLimit(result.stdout, output_limit)
        stderr, stderr_meta = _decodeAndLimit(result.stderr, output_limit)
        payload = {
            "success": True,
            "command": command,
            "shellCommand": shellCommand,
            "usesShell": shellCommand is not None,
            "advanced": shellCommand is not None,
            "cwd": str(workdir),
            "returnCode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "durationMs": duration_ms,
            "truncated": stdout_meta["truncated"] or stderr_meta["truncated"],
            "stdoutBytes": stdout_meta["originalBytes"],
            "stderrBytes": stderr_meta["originalBytes"],
            "stdoutReturnedBytes": stdout_meta["returnedBytes"],
            "stderrReturnedBytes": stderr_meta["returnedBytes"],
            "stdoutTruncated": stdout_meta["truncated"],
            "stderrTruncated": stderr_meta["truncated"],
        }
        _recordCommandResult(payload)
        return payload
    except subprocess.TimeoutExpired as exc:
        duration_ms = round((time.monotonic() - started) * 1000, 3)
        stdout, stdout_meta = _decodeAndLimit(exc.stdout or b"", output_limit)
        stderr, stderr_meta = _decodeAndLimit(exc.stderr or b"", output_limit)
        payload = {
            "success": False,
            "command": command,
            "shellCommand": shellCommand,
            "usesShell": shellCommand is not None,
            "advanced": shellCommand is not None,
            "cwd": str(workdir),
            "returnCode": None,
            "stdout": stdout,
            "stderr": stderr,
            "durationMs": duration_ms,
            "truncated": stdout_meta["truncated"] or stderr_meta["truncated"],
            "stdoutBytes": stdout_meta["originalBytes"],
            "stderrBytes": stderr_meta["originalBytes"],
            "stdoutReturnedBytes": stdout_meta["returnedBytes"],
            "stderrReturnedBytes": stderr_meta["returnedBytes"],
            "stdoutTruncated": stdout_meta["truncated"],
            "stderrTruncated": stderr_meta["truncated"],
            "timedOut": True,
            "errorMessage": f"Command timed out after {timeout}s",
        }
        _recordCommandResult(payload)
        return payload


def getCommandHistory(limit: int = 10) -> list[dict[str, Any]]:
    """Return recent command result summaries for the current MCP process."""
    max_items = max(1, int(limit))
    return list(_RECENT_COMMAND_RESULTS[-max_items:])


def _decodeAndLimit(data: bytes | str, maxBytes: int) -> tuple[str, dict[str, Any]]:
    if isinstance(data, str):
        raw = data.encode("utf-8", errors="replace")
    else:
        raw = data
    original_bytes = len(raw)
    truncated = len(raw) > maxBytes
    if truncated:
        raw = raw[:maxBytes]
    return raw.decode("utf-8", errors="replace"), {
        "originalBytes": original_bytes,
        "returnedBytes": len(raw),
        "truncated": truncated,
    }


def _recordCommandResult(payload: dict[str, Any]) -> None:
    _RECENT_COMMAND_RESULTS.append(
        {
            "command": payload.get("command"),
            "shellCommand": payload.get("shellCommand"),
            "usesShell": payload.get("usesShell", False),
            "advanced": payload.get("advanced", False),
            "cwd": payload.get("cwd"),
            "returnCode": payload.get("returnCode"),
            "success": payload.get("success"),
            "durationMs": payload.get("durationMs"),
            "timedOut": payload.get("timedOut", False),
            "truncated": payload.get("truncated", False),
            "stdoutBytes": payload.get("stdoutBytes", 0),
            "stderrBytes": payload.get("stderrBytes", 0),
        }
    )
    if len(_RECENT_COMMAND_RESULTS) > _MAX_RECENT_COMMAND_RESULTS:
        del _RECENT_COMMAND_RESULTS[: len(_RECENT_COMMAND_RESULTS) - _MAX_RECENT_COMMAND_RESULTS]
