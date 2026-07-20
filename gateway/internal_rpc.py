from __future__ import annotations

from typing import Any

from internal_rpc.models import InternalRpcRequest
from internal_rpc.server import InternalRpcServer
from pojo.ScheduledTask import ScheduledTaskCreate


_server: InternalRpcServer | None = None


def start_backend_rpc_server() -> None:
    global _server
    if _server is not None:
        return
    _server = InternalRpcServer(
        handlers={
            "scheduledTasks.create": _create_scheduled_task,
            "scheduledTasks.list": _list_scheduled_tasks,
            "scheduledTasks.delete": _delete_scheduled_task,
            "scheduledTasks.pause": _pause_scheduled_task,
            "scheduledTasks.resume": _resume_scheduled_task,
        }
    )
    _server.start()


def stop_backend_rpc_server() -> None:
    global _server
    if _server is None:
        return
    _server.stop()
    _server = None


def _caller_user_id(request: InternalRpcRequest) -> int:
    return int(request.caller.userId or 0)


def _create_scheduled_task(
    params: dict[str, Any],
    request: InternalRpcRequest,
) -> dict[str, Any]:
    from gateway.service.ScheduledTaskService import ScheduledTaskService

    task = ScheduledTaskService().createTask(
        _caller_user_id(request),
        ScheduledTaskCreate(
            name=str(params["name"]),
            cronExpression=str(params["cronExpression"]),
            taskDescription=str(params["taskDescription"]),
            approvalPolicy=params.get("approvalPolicy"),
        ),
    )
    return {
        "success": True,
        "task": task.model_dump(mode="json"),
        "message": f"定时任务 '{task.name}' 已创建",
    }


def _list_scheduled_tasks(
    params: dict[str, Any],
    _request: InternalRpcRequest,
) -> dict[str, Any]:
    from gateway.service.ScheduledTaskService import ScheduledTaskService

    status = params.get("status") or None
    result = ScheduledTaskService().listTasks(None, status=status)
    return {
        "success": True,
        "total": result.total,
        "items": [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in result.items
        ],
    }


def _delete_scheduled_task(
    params: dict[str, Any],
    _request: InternalRpcRequest,
) -> dict[str, Any]:
    from gateway.service.ScheduledTaskService import ScheduledTaskService

    task_id = int(params["taskId"])
    ScheduledTaskService().deleteTask(task_id, None)
    return {"success": True, "message": f"定时任务 {task_id} 已删除"}


def _pause_scheduled_task(
    params: dict[str, Any],
    _request: InternalRpcRequest,
) -> dict[str, Any]:
    from gateway.service.ScheduledTaskService import ScheduledTaskService

    task_id = int(params["taskId"])
    task = ScheduledTaskService().pauseTask(task_id, None)
    return {
        "success": True,
        "task": task.model_dump(mode="json"),
        "message": f"定时任务 {task_id} 已暂停",
    }


def _resume_scheduled_task(
    params: dict[str, Any],
    _request: InternalRpcRequest,
) -> dict[str, Any]:
    from gateway.service.ScheduledTaskService import ScheduledTaskService

    task_id = int(params["taskId"])
    task = ScheduledTaskService().resumeTask(task_id, None)
    return {
        "success": True,
        "task": task.model_dump(mode="json"),
        "message": f"定时任务 {task_id} 已恢复",
    }
