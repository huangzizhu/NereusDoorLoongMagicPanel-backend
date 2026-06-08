"""
进程管理工具 — 纯 /proc + subprocess，零外部依赖。

替代原 process/process_tools.py，去掉 psutil / pydantic / _command_runner。
"""
from __future__ import annotations
import os
import signal
import subprocess

from ndlmpanel_agent.shared.ops_types import (
    ProcessInfo, ProcessKillResult, BatchKillResult,
)
from ndlmpanel_agent.shared.types import ToolRiskLevel

TOOLS = {
    "listProcesses": ToolRiskLevel.READ_ONLY,
    "getProcessDetail": ToolRiskLevel.READ_ONLY,
    "getZombieOrphanProcesses": ToolRiskLevel.READ_ONLY,
    "killProcess": ToolRiskLevel.DANGEROUS,
    "batchKillProcesses": ToolRiskLevel.DANGEROUS,
}


def _run(argv: list[str], timeout: int = 15,
         check: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout,
            shell=False)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"超时: {' '.join(argv)}") from None
    except FileNotFoundError:
        raise RuntimeError(f"命令不存在: {argv[0]}") from None


def _readProcFile(path: str) -> str:
    try:
        with open(path) as f:
            return f.read().strip()
    except (FileNotFoundError, OSError):
        return ""


# ── 进程列表 ──

def listProcesses(sortBy: str = "cpu", limit: int = 50) -> list[ProcessInfo]:
    rows = []
    try:
        r = _run(["ps", "aux", "--no-headers",
                  "--sort=-%cpu" if sortBy != "pid" else "--sort=pid"], check=False)
        for i, line in enumerate(r.stdout.strip().split("\n")):
            if i >= limit:
                break
            parts = line.split(None, 10)
            if len(parts) >= 11:
                try:
                    rows.append(ProcessInfo(
                        pid=int(parts[1]), processName=parts[10].split()[0][:50],
                        userName=parts[0],
                        cpuPercent=float(parts[2]), memoryPercent=float(parts[3]),
                        status=parts[7], command=" ".join(parts[10:])[:200],
                    ))
                except (ValueError, IndexError):
                    pass
    except RuntimeError:
        pass
    return rows


# ── 进程详情 ──

def getProcessDetail(pid: int) -> dict:
    base = f"/proc/{pid}"
    try:
        stat = _readProcFile(f"{base}/stat")
    except Exception:
        return {"error": f"进程 {pid} 不存在或无权限访问"}

    parts = stat.split(") ", 1)
    if len(parts) < 2:
        return {"error": "无法解析 /proc/stat"}
    name = parts[0].lstrip("(")
    fields = parts[1].split()
    try:
        ppid = int(fields[1]) if len(fields) > 1 else None
    except ValueError:
        ppid = None

    statusInfo = {}
    for line in _readProcFile(f"{base}/status").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            statusInfo[k.strip()] = v.strip()

    cmdline = _readProcFile(f"{base}/cmdline").replace("\x00", " ")

    # RSS (常驻内存)
    rssBytes = None
    try:
        rssPages = int(fields[7]) if len(fields) > 7 else 0
        rssBytes = rssPages * os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else rssPages * 4096
    except (ValueError, IndexError):
        pass

    return {
        "pid": pid, "processName": name,
        "ppid": ppid, "status": statusInfo.get("State", "").split()[0],
        "userName": statusInfo.get("Uid", "").split()[-1],
        "command": cmdline[:300],
        "rssBytes": rssBytes,
        "threadCount": int(statusInfo.get("Threads", 0)) if statusInfo.get("Threads") else None,
        "cwd": os.readlink(f"{base}/cwd") if os.path.islink(f"{base}/cwd") else None,
    }


# ── 僵尸/孤儿进程 ──

def getZombieOrphanProcesses() -> list[ProcessInfo]:
    procs: list[ProcessInfo] = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            pid = int(entry)
            stat = _readProcFile(f"/proc/{entry}/stat")
            if not stat:
                continue
            afterParen = stat.split(") ", 1)
            if len(afterParen) < 2:
                continue
            name = afterParen[0].lstrip("(")
            fields = afterParen[1].split()
            st = fields[0] if fields else ""
            ppid = int(fields[1]) if len(fields) > 1 else 0

            isZombie = st == "Z"
            isOrphan = ppid == 1 and st != "Z"
            if not isZombie and not isOrphan:
                continue
            procs.append(ProcessInfo(
                pid=pid, processName=name, userName="",
                cpuPercent=0.0, memoryPercent=0.0,
                status="zombie" if isZombie else "orphan",
                command=_readProcFile(f"/proc/{entry}/cmdline").replace("\x00", " ")[:200],
                ppid=ppid,
            ))
        except (OSError, ValueError):
            continue
    return procs


# ── Kill ──

def killProcess(pid: int, signalNum: int = signal.SIGTERM) -> ProcessKillResult:
    try:
        os.kill(pid, signalNum)
        return ProcessKillResult(success=True, pid=pid)
    except ProcessLookupError:
        return ProcessKillResult(success=False, pid=pid, errorMessage="进程不存在")
    except PermissionError:
        return ProcessKillResult(success=False, pid=pid, errorMessage="权限不足")
    except OSError as exc:
        return ProcessKillResult(success=False, pid=pid, errorMessage=str(exc))


def batchKillProcesses(pids: list[int],
                       signalNum: int = signal.SIGTERM) -> BatchKillResult:
    results = [killProcess(pid, signalNum) for pid in pids]
    success = sum(1 for r in results if r.success)
    return BatchKillResult(results=results, totalRequested=len(pids),
                           totalSuccess=success, totalFailed=len(pids) - success)
