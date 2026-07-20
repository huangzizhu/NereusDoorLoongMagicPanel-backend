from __future__ import annotations

from agent.agent_core.agent_loop import AgentCore


def _core(policy: dict) -> AgentCore:
    core = object.__new__(AgentCore)
    core._scheduledApprovalPolicy = policy
    return core


def test_preapproval_allows_tool_and_path():
    core = _core({
        "allowedTools": ["writeFile"],
        "allowedPaths": ["/tmp/allowed"],
    })

    allowed, reason = core._isPreAuthorizedToolCall(
        "writeFile",
        {"path": "/tmp/allowed/report.txt", "content": "ok"},
    )

    assert allowed is True
    assert "匹配" in reason


def test_preapproval_denies_unlisted_tool():
    core = _core({
        "allowedTools": ["writeFile"],
        "allowedPaths": ["/tmp/allowed"],
    })

    allowed, reason = core._isPreAuthorizedToolCall(
        "deletePath",
        {"path": "/tmp/allowed/report.txt"},
    )

    assert allowed is False
    assert "allowedTools" in reason


def test_preapproval_denies_path_outside_allowed_paths():
    core = _core({
        "allowedTools": ["writeFile"],
        "allowedPaths": ["/tmp/allowed"],
    })

    allowed, reason = core._isPreAuthorizedToolCall(
        "writeFile",
        {"path": "/var/log/report.txt"},
    )

    assert allowed is False
    assert "allowedPaths" in reason


def test_preapproval_denies_denied_path_even_when_allowed_parent_matches():
    core = _core({
        "allowedTools": ["writeFile"],
        "allowedPaths": ["/tmp/allowed"],
        "deniedPaths": ["/tmp/allowed/secret"],
    })

    allowed, reason = core._isPreAuthorizedToolCall(
        "writeFile",
        {"path": "/tmp/allowed/secret/token.txt"},
    )

    assert allowed is False
    assert "deniedPaths" in reason


def test_preapproval_checks_submit_elevation_command_allowlist():
    core = _core({
        "allowedTools": ["submitElevation"],
        "allowedPrivilegedCommands": ["mkdir"],
    })

    allowed, reason = core._isPreAuthorizedToolCall(
        "submitElevation",
        {"commands": [{"command": "rm", "args": ["-rf", "/tmp/x"]}]},
    )

    assert allowed is False
    assert "特权命令未授权" in reason
