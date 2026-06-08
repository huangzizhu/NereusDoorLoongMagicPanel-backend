"""
网络诊断工具 — 纯 stdlib，零外部依赖。

替代原 network/network_tools.py，去掉 pydantic / _command_runner。
"""
from __future__ import annotations
import re
import socket
import subprocess
import time

from ndlmpanel_agent.shared.ops_types import PingResult, PortCheckResult
from ndlmpanel_agent.shared.types import ToolRiskLevel

TOOLS = {
    "pingHost": ToolRiskLevel.READ_ONLY,
    "checkPortConnectivity": ToolRiskLevel.READ_ONLY,
    "getListeningPorts": ToolRiskLevel.READ_ONLY,
}


def _run(argv: list[str], timeout: int = 15,
         check: bool = False) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout,
            shell=False)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(argv, -1, "", "timeout")
    except FileNotFoundError:
        return subprocess.CompletedProcess(argv, -1, "", f"not found: {argv[0]}")


def pingHost(host: str, timeout: int = 5) -> PingResult:
    try:
        r = _run(["ping", "-c", "4", "-W", str(timeout), host],
                 timeout=timeout * 5, check=False)
    except Exception:
        return PingResult(isReachable=False, packetLossPercent=100.0)

    lossMatch = re.search(r"([\d.]+)% packet loss", r.stdout)
    latencyMatch = re.search(r"rtt min/avg/max/mdev = [\d.]+/([\d.]+)/", r.stdout)
    return PingResult(
        isReachable=(r.returncode == 0),
        averageLatencyMs=float(latencyMatch.group(1)) if latencyMatch else None,
        packetLossPercent=float(lossMatch.group(1)) if lossMatch else None,
    )


def checkPortConnectivity(host: str, port: int, timeout: int = 5) -> PortCheckResult:
    start = time.time()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        elapsed = (time.time() - start) * 1000
        sock.close()
        return PortCheckResult(isOpen=True, connectionTimeMs=round(elapsed, 2))
    except (socket.timeout, ConnectionRefusedError, OSError):
        return PortCheckResult(isOpen=False)


def getListeningPorts() -> list[dict]:
    """获取 TCP/UDP 监听端口列表。"""
    results: list[dict] = []
    for flag in ("-tlnp", "-ulnp"):
        try:
            r = _run(["ss", flag], check=False)
            for line in r.stdout.strip().split("\n")[1:]:
                parts = line.split()
                if len(parts) >= 5:
                    results.append({
                        "protocol": "tcp" if "t" in flag else "udp",
                        "localAddress": parts[4],
                        "process": " ".join(parts[5:]) if len(parts) > 5 else "",
                    })
        except Exception:
            pass
    return results[:50]
