"""系统快照采集器 — 纯 /proc 读取 + subprocess。

为 Prompt L3 层提供结构化系统状态。
独立于 plugins/，避免循环依赖。
"""
from __future__ import annotations
import os, subprocess, time


def getSystemSnapshot() -> dict:
    """一次性采集系统快照。

    Returns:
        {
            "cpu": {...}, "memory": {...}, "disk": [...],
            "processes_top5": [...], "network": {...},
            "uptime_seconds": float, "uname": str
        }
    """
    return {
        "cpu": _collectCpu(),
        "memory": _collectMemory(),
        "disk": _collectDisk(),
        "processes_top5": _collectTopProcesses(),
        "network": _collectNetwork(),
        "uptime_seconds": _collectUptime(),
        "uname": _collectUname(),
    }


def _collectCpu() -> dict:
    model = "Unknown"
    cores = 0
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name") and model == "Unknown":
                    model = line.split(":", 1)[1].strip()
                if line.startswith("processor"):
                    cores += 1
    except FileNotFoundError:
        pass

    # CPU 使用率
    def _read():
        with open("/proc/stat") as f:
            for line in f:
                if line.startswith("cpu "):
                    p = [int(x) for x in line.split()[1:]]
                    return sum(p), p[3]
        return 0, 0

    t1, i1 = _read()
    time.sleep(0.3)
    t2, i2 = _read()
    usage = round(100.0 * (1 - (i2 - i1) / max(t2 - t1, 1)), 1)

    # 负载
    load1 = load5 = load15 = 0.0
    try:
        with open("/proc/loadavg") as f:
            parts = f.read().split()
            load1, load5, load15 = float(parts[0]), float(parts[1]), float(parts[2])
    except Exception:
        pass

    return {"model": model, "cores": cores, "usage_pct": usage,
            "load_1m": load1, "load_5m": load5, "load_15m": load15}


def _collectMemory() -> dict:
    mem = {"total_gb": 0, "used_gb": 0, "available_gb": 0,
           "usage_pct": 0, "swap_total_gb": 0, "swap_used_gb": 0}
    try:
        vals = {}
        with open("/proc/meminfo") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    vals[k.strip()] = int(v.strip().split()[0])
        total = vals.get("MemTotal", 0)
        avail = vals.get("MemAvailable", vals.get("MemFree", 0))
        swapTotal = vals.get("SwapTotal", 0)
        swapFree = vals.get("SwapFree", 0)
        mem["total_gb"] = round(total / 1048576, 1)
        mem["used_gb"] = round((total - avail) / 1048576, 1)
        mem["available_gb"] = round(avail / 1048576, 1)
        mem["usage_pct"] = round(100.0 * (total - avail) / max(total, 1), 1)
        mem["swap_total_gb"] = round(swapTotal / 1048576, 1)
        mem["swap_used_gb"] = round((swapTotal - swapFree) / 1048576, 1)
    except Exception:
        pass
    return mem


def _collectDisk() -> list[dict]:
    partitions = []
    try:
        result = subprocess.run(["df", "-h", "-x", "tmpfs", "-x", "devtmpfs",
                                 "-x", "squashfs"],
                                capture_output=True, text=True, timeout=10)
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 6:
                partitions.append({
                    "filesystem": parts[0], "size": parts[1],
                    "used": parts[2], "available": parts[3],
                    "use_pct": parts[4], "mount": parts[5],
                })
    except Exception:
        pass
    return partitions[:10]


def _collectTopProcesses() -> list[dict]:
    procs = []
    try:
        result = subprocess.run(
            ["ps", "aux", "--sort=-%cpu"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.strip().split("\n")[1:6]:
            parts = line.split()
            if len(parts) >= 11:
                procs.append({
                    "user": parts[0], "pid": parts[1],
                    "cpu": parts[2], "mem": parts[3],
                    "command": " ".join(parts[10:]),
                })
    except Exception:
        pass
    return procs


def _collectNetwork() -> dict:
    info = {"interfaces": [], "connections": 0}
    try:
        result = subprocess.run(
            ["ss", "-tunap"], capture_output=True, text=True, timeout=10,
        )
        lines = [l for l in result.stdout.strip().split("\n") if l]
        info["connections"] = len(lines) - 1
    except Exception:
        pass
    return info


def _collectUptime() -> float:
    try:
        with open("/proc/uptime") as f:
            return float(f.read().split()[0])
    except Exception:
        return 0.0


def _collectUname() -> str:
    try:
        r = subprocess.run(["uname", "-a"], capture_output=True,
                           text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return "Unknown"
