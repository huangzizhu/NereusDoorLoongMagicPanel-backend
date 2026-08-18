import ipaddress
import logging
import os
import re
import shutil
import subprocess
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from privileged_agent.models import PrivilegedErrorCode


logger = logging.getLogger("privileged_agent.firewall")


class PrivilegedAgentActionError(Exception):
    def __init__(self, code: PrivilegedErrorCode, message: str, details: str | None = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


@dataclass
class FirewallCommandResult:
    stdout: str
    stderr: str
    returncode: int


def _run_command(
    command: list[str],
    check: bool = True,
    timeout: int = 5,
) -> FirewallCommandResult:
    try:
        command_env = os.environ.copy()
        command_env["LC_ALL"] = "C"
        command_env["LANG"] = "C"
        command_env["LANGUAGE"] = "C"
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            env=command_env,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise PrivilegedAgentActionError(
            PrivilegedErrorCode.SERVICE_UNAVAILABLE,
            f"命令不存在: {command[0]}",
            str(exc),
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise PrivilegedAgentActionError(
            PrivilegedErrorCode.SERVICE_UNAVAILABLE,
            "系统命令执行超时",
            f"timeout={timeout}s command={' '.join(command)}",
        ) from exc
    except Exception as exc:
        raise PrivilegedAgentActionError(
            PrivilegedErrorCode.INTERNAL_ERROR,
            "执行系统命令失败",
            str(exc),
        ) from exc

    if check and result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        details = stderr or stdout or f"command={' '.join(command)} returncode={result.returncode}"
        raise PrivilegedAgentActionError(
            PrivilegedErrorCode.COMMAND_FAILED,
            "系统命令执行失败",
            details,
        )

    return FirewallCommandResult(
        stdout=result.stdout or "",
        stderr=result.stderr or "",
        returncode=result.returncode,
    )


def detect_backend() -> str:
    if shutil.which("firewall-cmd"):
        return "firewalld"
    if shutil.which("ufw"):
        return "ufw"
    raise PrivilegedAgentActionError(
        PrivilegedErrorCode.SERVICE_UNAVAILABLE,
        "未检测到受支持的防火墙服务",
        "未发现 firewall-cmd 或 ufw",
    )


def _detect_ip_family(source_ip: str | None = None, destination_ip: str | None = None) -> int:
    for value in [source_ip, destination_ip]:
        if not value:
            continue
        candidate = str(value).strip()
        if not candidate:
            continue
        try:
            network = ipaddress.ip_network(candidate, strict=False)
            return network.version
        except ValueError:
            pass
    return 4


def _default_any_for_family(ip_version: int) -> str:
    return "::/0" if ip_version == 6 else "0.0.0.0/0"


def get_firewall_status() -> dict[str, object]:
    backend = detect_backend()
    if backend == "firewalld":
        state_result = _run_command(["firewall-cmd", "--state"], check=False)
        is_active = "running" in state_result.stdout.strip().lower()
        default_policy = "unknown"
        if is_active:
            zone_result = _run_command(["firewall-cmd", "--get-default-zone"])
            default_policy = zone_result.stdout.strip() or "unknown"
        return {
            "backendType": backend,
            "isActive": is_active,
            "defaultPolicy": default_policy,
        }

    verbose_result = _run_command(["ufw", "status", "verbose"])
    output = verbose_result.stdout or ""
    logger.info(
        "ufw status verbose stdout=%r stderr=%r returncode=%s",
        verbose_result.stdout,
        verbose_result.stderr,
        verbose_result.returncode,
    )
    lower_output = output.lower()
    if re.search(r"^\s*status:\s*active\b", lower_output, re.MULTILINE):
        is_active = True
    elif re.search(r"^\s*status:\s*inactive\b", lower_output, re.MULTILINE):
        is_active = False
    elif re.search(r"^\s*to\s+action\s+from\s*$", lower_output, re.MULTILINE):
        is_active = True
    else:
        raise PrivilegedAgentActionError(
            PrivilegedErrorCode.COMMAND_FAILED,
            "无法解析 ufw 状态输出",
            output.strip() or "empty stdout",
        )
    default_policy = "unknown"
    matched = re.search(r"Default:\s*(.+)", output)
    if matched:
        default_policy = matched.group(1).strip()
    return {
        "backendType": backend,
        "isActive": is_active,
        "defaultPolicy": default_policy,
    }


def list_firewall_rules() -> list[dict[str, object]]:
    backend = detect_backend()
    rules: list[dict[str, object]] = []
    if backend == "firewalld":
        port_result = _run_command(["firewall-cmd", "--list-ports"])
        for entry in port_result.stdout.strip().split():
            if "/" not in entry:
                continue
            port_text, protocol = entry.split("/", 1)
            for ip_version in [4, 6]:
                rules.append(
                    {
                        "port": int(port_text),
                        "protocol": protocol.lower(),
                        "policy": "accept",
                        "sourceIp": None,
                        "destinationIp": None,
                        "ipVersion": ip_version,
                    }
                )

        rich_result = _run_command(["firewall-cmd", "--list-rich-rules"], check=False)
        for line in rich_result.stdout.strip().splitlines():
            port_match = re.search(r'port port="(\d+)" protocol="(\w+)"', line)
            source_match = re.search(r'source address="([^"]+)"', line)
            action_match = re.search(r"(accept|reject|drop)", line)
            family_match = re.search(r'family="(ipv4|ipv6)"', line)
            if not port_match:
                continue
            ip_version = 6 if family_match and family_match.group(1) == "ipv6" else 4
            rules.append(
                {
                    "port": int(port_match.group(1)),
                    "protocol": port_match.group(2).lower(),
                    "policy": (action_match.group(1) if action_match else "accept").lower(),
                    "sourceIp": source_match.group(1) if source_match else None,
                    "destinationIp": None,
                    "ipVersion": ip_version,
                }
            )
        return rules

    status_result = _run_command(["ufw", "status"])
    output = status_result.stdout or ""
    logger.info(
        "ufw status stdout=%r stderr=%r returncode=%s",
        status_result.stdout,
        status_result.stderr,
        status_result.returncode,
    )
    table_started = False
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith("status:"):
            continue
        if line.startswith("--"):
            table_started = True
            continue
        if not table_started:
            continue

        columns = re.split(r"\s{2,}", line)
        if len(columns) < 3:
            continue

        target_text = columns[0].strip()
        action_text = columns[1].strip()
        source_text = columns[2].strip()

        port_match = re.match(r"^(\d+)/(tcp|udp)(?:\s+\(v6\))?$", target_text, re.IGNORECASE)
        if not port_match:
            continue

        ip_version = 6 if "(v6)" in target_text.lower() or "(v6)" in source_text.lower() else 4
        policy = action_text.split()[0].lower()
        normalized_source = source_text
        if normalized_source.lower() in ["anywhere", "anywhere (v6)"]:
            normalized_source = None

        rules.append(
            {
                "port": int(port_match.group(1)),
                "protocol": port_match.group(2).lower(),
                "policy": policy,
                "sourceIp": normalized_source,
                "destinationIp": None,
                "ipVersion": ip_version,
            }
        )
    return rules


def add_port_rule(
    port: int,
    protocol: str,
    ip_version: int | None = None,
    source_ip: str | None = None,
    destination_ip: str | None = None,
    action: int = 1,
) -> dict[str, object]:
    if action != 1:
        raise PrivilegedAgentActionError(
            PrivilegedErrorCode.INVALID_REQUEST,
            "当前仅支持新增允许规则",
            f"action={action}",
        )

    ip_version = ip_version or _detect_ip_family(source_ip, destination_ip)
    source_ip = source_ip or _default_any_for_family(ip_version)
    destination_ip = destination_ip or _default_any_for_family(ip_version)

    if _detect_ip_family(source_ip) != _detect_ip_family(destination_ip):
        raise PrivilegedAgentActionError(
            PrivilegedErrorCode.INVALID_REQUEST,
            "IPv4 和 IPv6 地址不能混用",
            f"source={source_ip}, destination={destination_ip}",
        )

    backend = detect_backend()
    normalized_protocol = protocol.lower()
    if backend == "firewalld":
        family = "ipv6" if ip_version == 6 else "ipv4"
        if source_ip != _default_any_for_family(ip_version):
            _run_command(
                [
                    "firewall-cmd",
                    "--permanent",
                    "--add-rich-rule",
                    f'rule family="{family}" source address="{source_ip}" port port="{port}" protocol="{normalized_protocol}" accept',
                ]
            )
        else:
            _run_command(["firewall-cmd", f"--add-port={port}/{normalized_protocol}", "--permanent"])
        _run_command(["firewall-cmd", "--reload"])
    else:
        command = [
            "ufw",
            "allow",
            "proto",
            normalized_protocol,
            "from",
            source_ip,
            "to",
            "any",
            "port",
            str(port),
        ]
        _run_command(command)

    return {
        "port": port,
        "protocol": normalized_protocol,
        "policy": "accept",
        "sourceIp": source_ip,
        "destinationIp": destination_ip,
        "ipVersion": ip_version,
    }


def remove_port_rule(
    port: int,
    protocol: str,
    ip_version: int | None = None,
    source_ip: str | None = None,
    destination_ip: str | None = None,
) -> dict[str, object]:
    ip_version = ip_version or _detect_ip_family(source_ip, destination_ip)
    source_ip = source_ip or _default_any_for_family(ip_version)
    destination_ip = destination_ip or _default_any_for_family(ip_version)

    if _detect_ip_family(source_ip) != _detect_ip_family(destination_ip):
        raise PrivilegedAgentActionError(
            PrivilegedErrorCode.INVALID_REQUEST,
            "IPv4 和 IPv6 地址不能混用",
            f"source={source_ip}, destination={destination_ip}",
        )

    backend = detect_backend()
    normalized_protocol = protocol.lower()
    if backend == "firewalld":
        family = "ipv6" if ip_version == 6 else "ipv4"
        if source_ip != _default_any_for_family(ip_version):
            _run_command(
                [
                    "firewall-cmd",
                    "--permanent",
                    "--remove-rich-rule",
                    f'rule family="{family}" source address="{source_ip}" port port="{port}" protocol="{normalized_protocol}" accept',
                ]
            )
        else:
            _run_command(["firewall-cmd", f"--remove-port={port}/{normalized_protocol}", "--permanent"])
        _run_command(["firewall-cmd", "--reload"])
    else:
        command = [
            "ufw",
            "--force",
            "delete",
            "allow",
            "proto",
            normalized_protocol,
            "from",
            source_ip,
            "to",
            "any",
            "port",
            str(port),
        ]
        _run_command(command)

    return {
        "port": port,
        "protocol": normalized_protocol,
        "policy": "removed",
        "sourceIp": source_ip,
        "destinationIp": destination_ip,
        "ipVersion": ip_version,
    }


def set_firewall_enabled(enabled: bool) -> dict[str, object]:
    backend = detect_backend()
    if backend == "firewalld":
        command = ["systemctl", "start" if enabled else "stop", "firewalld"]
        _run_command(command)
        status = get_firewall_status()
        return {
            "backendType": backend,
            "enabled": bool(status["isActive"]),
        }

    _run_command(["ufw", "--force", "enable" if enabled else "disable"])
    status = get_firewall_status()
    return {
        "backendType": backend,
        "enabled": bool(status["isActive"]),
    }


def list_ssh_logs(max_lines: int = 500) -> list[dict[str, object]]:
    lines = _read_ssh_log_lines(max_lines=max_lines)
    parsed_logs: list[dict[str, object]] = []
    for idx, line in enumerate(lines):
        parsed = _parse_ssh_log_line(line)
        if parsed is None:
            continue
        parsed["id"] = idx + 1
        parsed_logs.append(parsed)
    return parsed_logs


def _read_ssh_log_lines(max_lines: int = 500) -> list[str]:
    journal_lines = _read_journal_ssh_logs(max_lines=max_lines)
    if journal_lines:
        return journal_lines
    for log_path in [Path("/var/log/auth.log"), Path("/var/log/secure")]:
        file_lines = _read_tail_lines(log_path, max_lines=max_lines)
        if file_lines:
            return file_lines
    return []


def _read_journal_ssh_logs(max_lines: int = 500) -> list[str]:
    services = [["ssh"], ["sshd"], ["ssh", "sshd"]]
    for service_names in services:
        command = ["journalctl", "--no-pager", "-o", "short-iso", "-n", str(max_lines), "-r"]
        for service_name in service_names:
            command.extend(["-u", service_name])
        result = _run_command(command, check=False, timeout=3)
        if result.returncode == 0 and result.stdout.strip():
            return [line for line in result.stdout.splitlines() if line.strip()]
    return []


def _read_tail_lines(path: Path, max_lines: int = 500) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fp:
            return list(deque(fp, maxlen=max_lines))
    except Exception:
        return []


def _parse_ssh_log_line(line: str) -> dict[str, object] | None:
    text = line.strip()
    if "sshd" not in text.lower():
        return None

    timestamp = _parse_log_timestamp(text)
    if timestamp is None:
        return None

    success_patterns = [
        re.compile(
            r"Accepted\s+(?P<method>\w+)\s+for\s+(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
            re.IGNORECASE,
        ),
    ]
    failure_patterns = [
        re.compile(
            r"Failed\s+\w+\s+for\s+(?:invalid user\s+)?(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
            re.IGNORECASE,
        ),
        re.compile(
            r"Invalid user\s+(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
            re.IGNORECASE,
        ),
    ]

    for pattern in success_patterns:
        matched = pattern.search(text)
        if matched:
            method = matched.groupdict().get("method", "")
            return {
                "timestamp": timestamp.isoformat(),
                "user": matched.group("user"),
                "sourceIp": matched.group("ip"),
                "port": int(matched.group("port")),
                "status": "SUCCESS",
                "reason": f"Accepted {method}".strip(),
            }

    for pattern in failure_patterns:
        matched = pattern.search(text)
        if matched:
            reason = "Authentication failed"
            if "invalid user" in text.lower():
                reason = "Invalid user"
            return {
                "timestamp": timestamp.isoformat(),
                "user": matched.group("user"),
                "sourceIp": matched.group("ip"),
                "port": int(matched.group("port")),
                "status": "FAILURE",
                "reason": reason,
            }
    return None


def _parse_log_timestamp(line: str) -> datetime | None:
    iso_match = re.match(r"^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:[+-]\d{4}|Z)?)", line)
    if iso_match:
        timestamp_text = iso_match.group("timestamp").replace(",", ".")
        if timestamp_text.endswith("Z"):
            timestamp_text = timestamp_text[:-1] + "+00:00"
        elif re.match(r".*[+-]\d{4}$", timestamp_text):
            timestamp_text = timestamp_text[:-5] + timestamp_text[-5:-2] + ":" + timestamp_text[-2:]
        try:
            return datetime.fromisoformat(timestamp_text)
        except ValueError:
            pass

    syslog_match = re.match(r"^(?P<stamp>[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})", line)
    if syslog_match:
        stamp = f"{datetime.now().year} {syslog_match.group('stamp')}"
        try:
            return datetime.strptime(stamp, "%Y %b %d %H:%M:%S")
        except ValueError:
            return None
    return None
