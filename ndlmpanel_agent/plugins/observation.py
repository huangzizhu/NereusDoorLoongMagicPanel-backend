"""
系统观察工具 — 纯 /proc + subprocess，零外部依赖。

合并原 monitor/system_monitor_tools + misc/system_info_tools + user/user_tools，
去掉 psutil / pydantic / _command_runner。
"""
from __future__ import annotations
import json
import os
import pwd
import socket
import subprocess
import time

from ndlmpanel_agent.shared.ops_types import (
    CpuInfo, MemoryInfo, DiskPartitionInfo, GpuInfo, NetworkInterfaceInfo,
    UserInfo, LoginRecord,
)
from ndlmpanel_agent.shared.types import ToolRiskLevel

TOOLS = {
    "getCpuInfo": ToolRiskLevel.READ_ONLY,
    "getMemoryInfo": ToolRiskLevel.READ_ONLY,
    "getDiskInfo": ToolRiskLevel.READ_ONLY,
    "getGpuInfo": ToolRiskLevel.READ_ONLY,
    "getNetworkInfo": ToolRiskLevel.READ_ONLY,
    "getSystemVersion": ToolRiskLevel.READ_ONLY,
    "getUptime": ToolRiskLevel.READ_ONLY,
    "listUsers": ToolRiskLevel.READ_ONLY,
    "getLoginHistory": ToolRiskLevel.READ_ONLY,
}


def _safeReadProc(path: str, default: str = "") -> str:
    try:
        with open(path) as f:
            return f.read().strip()
    except (FileNotFoundError, OSError):
        return default


def _run(argv: list[str], timeout: int = 15) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"命令超时({timeout}s): {' '.join(argv)}")
    except FileNotFoundError:
        raise RuntimeError(f"命令不存在: {argv[0]}") from None


# ── CPU ──

def getCpuInfo() -> CpuInfo:
    modelName = "Unknown"
    coreCount = 0
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name") and modelName == "Unknown":
                    modelName = line.split(":", 1)[1].strip()
                if line.startswith("processor"):
                    coreCount += 1
    except FileNotFoundError:
        coreCount = max(1, os.cpu_count() or 1)

    # 使用率：两次采样
    def _readStat():
        with open("/proc/stat") as f:
            for line in f:
                if line.startswith("cpu "):
                    p = [int(x) for x in line.split()[1:]]
                    return sum(p), p[3]
        return 0, 0
    t1, i1 = _readStat()
    time.sleep(0.5)
    t2, i2 = _readStat()
    usage = round(100.0 * (1 - (i2 - i1) / max(t2 - t1, 1)), 1)

    load1 = load5 = load15 = 0.0
    try:
        parts = _safeReadProc("/proc/loadavg").split()
        if len(parts) >= 3:
            load1, load5, load15 = float(parts[0]), float(parts[1]), float(parts[2])
    except (ValueError, IndexError):
        pass

    return CpuInfo(modelName=modelName, coreCount=coreCount,
                   usagePercent=usage, load1Min=load1, load5Min=load5, load15Min=load15)


# ── 内存 ──

def getMemoryInfo() -> MemoryInfo:
    vals: dict[str, int] = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    try:
                        vals[k.strip()] = int(v.strip().split()[0])
                    except ValueError:
                        pass
    except FileNotFoundError:
        pass
    total = vals.get("MemTotal", 0)
    avail = vals.get("MemAvailable", vals.get("MemFree", 0))
    swapTotal = vals.get("SwapTotal", 0)
    swapFree = vals.get("SwapFree", 0)
    return MemoryInfo(
        totalBytes=total * 1024, usedBytes=(total - avail) * 1024,
        availableBytes=avail * 1024,
        usagePercent=round(100.0 * (total - avail) / max(total, 1), 1),
        swapTotalBytes=swapTotal * 1024, swapUsedBytes=(swapTotal - swapFree) * 1024,
        swapUsagePercent=round(100.0 * (swapTotal - swapFree) / max(swapTotal, 1), 1) if swapTotal else 0.0,
    )


# ── 磁盘 ──

def getDiskInfo() -> list[DiskPartitionInfo]:
    results: list[DiskPartitionInfo] = []
    try:
        r = _run(["df", "-B1", "-x", "tmpfs", "-x", "devtmpfs", "-x", "squashfs"])
        for line in r.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 6:
                try:
                    results.append(DiskPartitionInfo(
                        mountPoint=parts[5], fileSystem=parts[0],
                        totalBytes=int(parts[1]), usedBytes=int(parts[2]),
                        usagePercent=float(parts[4].rstrip("%")),
                    ))
                except (ValueError, IndexError):
                    pass
    except RuntimeError:
        pass
    return results


# ── GPU ──

def getGpuInfo() -> list[GpuInfo]:
    try:
        r = _run(["nvidia-smi",
                  "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu",
                  "--format=csv,noheader,nounits"])
    except RuntimeError:
        return []
    gpus: list[GpuInfo] = []
    for line in r.stdout.strip().splitlines():
        p = [x.strip() for x in line.split(",")]
        if len(p) < 5:
            continue
        try:
            gpus.append(GpuInfo(modelName=p[0], memoryTotalMB=int(float(p[1])),
                                memoryUsedMB=int(float(p[2])),
                                utilizationPercent=float(p[3]),
                                temperatureCelsius=float(p[4])))
        except (ValueError, IndexError):
            continue
    return gpus


# ── 网络接ロ ──

def getNetworkInfo() -> list[NetworkInterfaceInfo]:
    results: list[NetworkInterfaceInfo] = []
    try:
        r = _run(["ip", "-j", "addr"])
        data = json.loads(r.stdout)
        for iface in data:
            name = iface.get("ifname", "")
            ipAddr = None
            macAddr = None
            for addr in iface.get("addr_info", []):
                if addr.get("family") == "inet" and ipAddr is None:
                    ipAddr = addr.get("local")
            macAddr = iface.get("address")
            isUp = iface.get("flags", [])
            results.append(NetworkInterfaceInfo(
                interfaceName=name, ipAddress=ipAddr, macAddress=macAddr,
                isUp="UP" in str(isUp).upper() if isinstance(isUp, list) else False,
            ))
    except (RuntimeError, json.JSONDecodeError):
        pass
    return results


# ── 系统版本 ──

def getSystemVersion() -> dict:
    osName = "Unknown"
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    osName = line.split("=", 1)[1].strip().strip('"')
                    break
    except FileNotFoundError:
        pass
    try:
        kernel = _run(["uname", "-r"]).stdout.strip()
    except RuntimeError:
        kernel = "Unknown"
    return {"osName": osName, "kernelVersion": kernel,
            "hostName": socket.gethostname()}


# ── 运行时间 ──

def getUptime() -> dict:
    try:
        uptimeSec = float(_safeReadProc("/proc/uptime").split()[0])
    except (ValueError, IndexError):
        uptimeSec = 0.0
    days = int(uptimeSec // 86400)
    hours = int(uptimeSec % 86400 // 3600)
    minutes = int(uptimeSec % 3600 // 60)
    return {"uptimeSeconds": uptimeSec, "days": days, "hours": hours,
            "minutes": minutes,
            "formatted": f"{days}天 {hours}小时 {minutes}分钟"}


# ── 用户 ──

def listUsers() -> list[UserInfo]:
    sudoUsers: set[str] = set()
    for grp in ("sudo", "wheel"):
        try:
            r = _run(["getent", "group", grp])
            if r.returncode == 0:
                parts = r.stdout.strip().split(":")
                if len(parts) >= 4 and parts[3]:
                    sudoUsers.update(parts[3].split(","))
        except RuntimeError:
            pass
    users: list[UserInfo] = []
    try:
        for p in pwd.getpwall():
            if p.pw_uid < 1000 and p.pw_uid != 0:
                continue
            users.append(UserInfo(userName=p.pw_name, uid=p.pw_uid,
                                  homeDirectory=p.pw_dir, loginShell=p.pw_shell,
                                  isSudoUser=(p.pw_name in sudoUsers or p.pw_uid == 0)))
    except Exception:
        pass
    return users


def getLoginHistory() -> list[LoginRecord]:
    try:
        r = _run(["last", "-n", "50", "-i", "-F"])
    except RuntimeError:
        return []
    records: list[LoginRecord] = []
    for line in r.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[0] in ("reboot", "wtmp", ""):
            continue
        userName = parts[0]
        loginIp = parts[2] if len(parts) > 2 and "." in parts[2] else None
        status = "success"
        if "still logged in" in line:
            status = "online"
        elif "gone - no logout" in line:
            status = "abnormal"
        records.append(LoginRecord(userName=userName, loginIp=loginIp,
                                   loginTime=" ".join(parts[3:7]) if len(parts) > 6 else " ".join(parts[3:]),
                                   loginStatus=status))
    return records
