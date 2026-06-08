import os
import platform
from datetime import datetime

import psutil

from utils.toolFunction.models.ops.misc.system_info_models import SystemVersion, UptimeInfo


def getSystemVersion() -> SystemVersion:
    osName = f"{platform.system()} {platform.release()}"

    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    osName = line.split("=", 1)[1].strip().strip('"')
                    break
    except FileNotFoundError:
        pass

    return SystemVersion(
        osName=osName,
        kernelVersion=platform.release(),
        hostName=platform.node(),
    )


def getUptime() -> UptimeInfo:
    now = datetime.now().astimezone()
    bootTime = datetime.fromtimestamp(psutil.boot_time(), tz=now.tzinfo)
    delta = now - bootTime
    totalSeconds = int(delta.total_seconds())
    offset = bootTime.strftime("%z")
    formattedOffset = f"{offset[:3]}:{offset[3:]}" if offset else None

    return UptimeInfo(
        days=totalSeconds // 86400,
        hours=(totalSeconds % 86400) // 3600,
        minutes=(totalSeconds % 3600) // 60,
        bootTime=bootTime,
        bootTimeTimezone=bootTime.tzname(),
        bootTimeUtcOffset=formattedOffset,
    )


def getEnvironmentVariables() -> dict[str, str]:
    return dict(os.environ)
