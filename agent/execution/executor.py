"""最小权限命令执行器。"""
from __future__ import annotations
import subprocess
import os

_SAFE_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"


def runCommand(argv: list[str], timeout: int = 30,
               runAs: str = "nobody", allowedPaths: list[str] | None = None,
               deniedPaths: list[str] | None = None,
               maxOutputBytes: int = 65536) -> tuple[bool, str, str]:
    """安全执行 OS 命令。

    Args:
        argv: 命令和参数
        timeout: 超时秒数
        runAs: 以哪个用户执行（默认 nobody）
        allowedPaths: 允许操作的路径白名单
        deniedPaths: 禁止操作的路径黑名单
        maxOutputBytes: stdout 最大输出字节

    Returns:
        (success, stdout, stderr)
    """
    # 路径安全检查
    if deniedPaths:
        for arg in argv:
            argStr = str(arg)
            for denied in deniedPaths:
                if argStr.startswith(denied) or denied in argStr:
                    return False, "", f"拒绝: 参数 {argStr} 命中黑名单路径 {denied}"

    if allowedPaths:
        for arg in argv:
            argStr = str(arg)
            if argStr.startswith("/") and not any(
                argStr.startswith(p) for p in allowedPaths
            ):
                return False, "", f"拒绝: 路径 {argStr} 不在白名单中"

    # 环境清洗
    safeEnv = {
        "PATH": _SAFE_PATH,
        "HOME": "/tmp",
        "LANG": os.environ.get("LANG", "C.UTF-8"),
    }

    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True,
            timeout=timeout, env=safeEnv,
            shell=False,  # 严禁 shell 注入
        )

        stdout = proc.stdout[:maxOutputBytes] if proc.stdout else ""
        stderr = proc.stderr[:maxOutputBytes] if proc.stderr else ""
        success = proc.returncode == 0

        return success, stdout, stderr

    except subprocess.TimeoutExpired:
        return False, "", f"命令超时 ({timeout}s): {' '.join(argv)}"
    except FileNotFoundError:
        return False, "", f"命令不存在: {argv[0]}"
    except Exception as exc:
        return False, "", str(exc)
