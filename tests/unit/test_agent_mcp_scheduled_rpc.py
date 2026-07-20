from __future__ import annotations

from agent.agent_mcp.server import tool_adapter
from internal_rpc import BackendRpcError


class _FakeClient:
    calls: list[tuple[str, dict]] = []
    response = {"success": True, "marker": "ok"}
    error: BackendRpcError | None = None

    def call(self, method, params):
        self.calls.append((method, params))
        if self.error:
            raise self.error
        return self.response


def test_create_scheduled_task_calls_backend_rpc(monkeypatch):
    _FakeClient.calls = []
    _FakeClient.response = {"success": True, "task": {"id": 1}}
    _FakeClient.error = None
    monkeypatch.setattr(tool_adapter, "BackendRpcClient", _FakeClient)

    result = tool_adapter.createScheduledTask("daily", "0 8 * * *", "run")

    assert result == {"success": True, "task": {"id": 1}}
    assert _FakeClient.calls == [
        (
            "scheduledTasks.create",
            {
                "name": "daily",
                "cronExpression": "0 8 * * *",
                "taskDescription": "run",
            },
        )
    ]


def test_scheduled_task_backend_rpc_error_is_structured(monkeypatch):
    _FakeClient.calls = []
    _FakeClient.response = {"success": True}
    _FakeClient.error = BackendRpcError(
        "SERVICE_UNAVAILABLE",
        "后端内部 RPC 不可用",
        "missing.sock",
    )
    monkeypatch.setattr(tool_adapter, "BackendRpcClient", _FakeClient)

    result = tool_adapter.listScheduledTasks()

    assert result == {
        "success": False,
        "errorCode": "SERVICE_UNAVAILABLE",
        "errorMessage": "后端内部 RPC 不可用",
        "errorDetails": "missing.sock",
    }
