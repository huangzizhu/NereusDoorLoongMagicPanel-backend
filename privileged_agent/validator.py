"""命令注册表加载与参数校验。

从 conf/privileged_commands.yaml 加载允许的命令定义，
并提供验证函数验证命令和参数是否合规。

特权代理启动时加载一次，此后注册表是只读的。
"""

import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml


class CommandNotRegisteredError(ValueError):
    """命令不在注册表中。"""

    def __init__(self, command: str):
        self.command = command
        super().__init__(f"命令 '{command}' 不在注册表中")


class ArgumentValidationError(ValueError):
    """参数校验失败。"""

    def __init__(self, command: str, reason: str):
        self.command = command
        super().__init__(f"命令 '{command}' 参数校验失败: {reason}")


class PathNotAllowedError(ValueError):
    """路径不在白名单内。"""

    def __init__(self, command: str, path: str):
        self.command = command
        self.path = path
        super().__init__(f"命令 '{command}' 路径 '{path}' 不在允许的父目录中")


class CommandRule:
    """解析后的单条命令规则。"""

    def __init__(self, name: str, raw: dict[str, Any]):
        self.name = name
        self.description = raw.get("description", "")
        self.risk = raw.get("risk", "write")
        self.command_line = raw.get("command_line")
        self.path_validation = raw.get("path_validation")
        self.allowed_args = raw.get("allowed_args")
        self.allowed_sql_prefixes = raw.get("allowed_sql_prefixes")

    def validate(self, args: list[str]) -> None:
        """校验命令参数是否合规。

        Args:
            args: 命令参数列表（不含命令名本身）

        Raises:
            ArgumentValidationError: 参数不合规
            PathNotAllowedError:    路径不在白名单
        """
        # 固定命令行的命令不接受额外参数
        if self.command_line:
            if args:
                raise ArgumentValidationError(
                    self.name,
                    f"固定命令 '{self.command_line}' 不接受额外参数: {args}",
                )
            return

        # 校验 allowed_args
        if self.allowed_args:
            self._validate_allowed_args(args)

        # 校验路径
        if self.path_validation:
            self._validate_paths(args)

        # 校验 SQL 前缀
        if self.allowed_sql_prefixes and args:
            self._validate_sql_prefix(args)

    def _validate_allowed_args(self, args: list[str]) -> None:
        aa = self.allowed_args

        # 校验 actions (systemctl 子命令)
        if "actions" in aa and args:
            if args[0] not in aa["actions"]:
                raise ArgumentValidationError(
                    self.name,
                    f"不支持的动作 '{args[0]}'，允许: {aa['actions']}",
                )

        # 校验 services (systemctl 服务名)
        if "services" in aa and len(args) > 1:
            # args[1] 是服务名
            if args[1] not in aa["services"]:
                raise ArgumentValidationError(
                    self.name,
                    f"不支持的服务 '{args[1]}'，允许: {aa['services']}",
                )

        # 校验 subcommands (certbot / firewall-cmd 子命令)
        if "subcommands" in aa and args:
            if args[0] not in aa["subcommands"]:
                raise ArgumentValidationError(
                    self.name,
                    f"不支持的子命令 '{args[0]}'，允许: {aa['subcommands']}",
                )

        # 校验 flags 白名单 (仅允许指定 flag)
        if "flags" in aa:
            for arg in args:
                if arg.startswith("--") or arg.startswith("-") and len(arg) > 1:
                    if arg not in aa["flags"]:
                        raise ArgumentValidationError(
                            self.name,
                            f"不允许的 flag '{arg}'，允许: {aa['flags']}",
                        )

        # 校验 mode_regex (chmod)
        if "mode_regex" in aa:
            for arg in args:
                if re.match(r"^0[0-7]{3}$", arg):
                    continue
                # 可能是一个路径而不是 mode
                if arg.startswith("/"):
                    continue
                if not re.match(aa["mode_regex"], arg):
                    raise ArgumentValidationError(
                        self.name,
                        f"参数 '{arg}' 不符合 mode 格式 '{aa['mode_regex']}'",
                    )

    def _validate_paths(self, args: list[str]) -> None:
        allowed = self.path_validation.get("allowed_parents", [])
        max_size = self.path_validation.get("max_size", 0)
        allowed_resolved = [Path(p).resolve() for p in allowed]

        for arg in args:
            # 跳过 flags
            if arg.startswith("-"):
                continue
            path = Path(arg)

            # 相对路径不校验（可能是 mkdir -p 的中间参数）
            if not path.is_absolute():
                continue

            try:
                resolved = path.resolve()
            except (OSError, RuntimeError):
                raise PathNotAllowedError(self.name, arg)

            # 检查是否在允许的父目录下
            allowed_flag = False
            for parent in allowed_resolved:
                try:
                    resolved.relative_to(parent)
                    allowed_flag = True
                    break
                except ValueError:
                    continue

            if not allowed_flag:
                raise PathNotAllowedError(self.name, arg)

            # 检查文件大小限制（仅对 write_file）
            if max_size > 0 and path.exists() and path.is_file():
                if path.stat().st_size > max_size:
                    raise ArgumentValidationError(
                        self.name,
                        f"文件 '{arg}' 大小超过限制 {max_size} 字节",
                    )

    def _validate_sql_prefix(self, args: list[str]) -> None:
        sql = " ".join(args).strip().upper()
        allowed_prefixes = [p.upper() for p in self.allowed_sql_prefixes]
        for prefix in allowed_prefixes:
            if sql.startswith(prefix):
                return
        raise ArgumentValidationError(
            self.name,
            f"SQL 语句必须以允许的前缀开头，允许: {self.allowed_sql_prefixes}",
        )


class CommandRegistry:
    """命令注册表 — 加载 YAML 并提供查询。"""

    _DEFAULT_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "conf",
        "privileged_commands.yaml",
    )

    def __init__(self, yaml_path: Optional[str] = None):
        self._path = yaml_path or self._DEFAULT_PATH
        self._rules: dict[str, CommandRule] = {}
        self._load()

    def _load(self) -> None:
        path = Path(self._path)
        if not path.exists():
            raise FileNotFoundError(f"命令注册表文件不存在: {self._path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        commands = data.get("commands", {})
        for name, raw in commands.items():
            self._rules[name] = CommandRule(name, raw)

    def lookup(self, command: str) -> CommandRule:
        """查找命令规则，不存在则抛出异常。"""
        rule = self._rules.get(command)
        if rule is None:
            raise CommandNotRegisteredError(command)
        return rule

    def has(self, command: str) -> bool:
        """命令是否在注册表中。"""
        return command in self._rules

    def list_commands(self) -> list[str]:
        """返回所有已注册的命令名列表（按风险分组）。"""
        return sorted(self._rules.keys())

    def list_by_risk(self, risk: str) -> list[dict[str, str]]:
        """按风险等级列出命令。"""
        result = []
        for name, rule in self._rules.items():
            if rule.risk == risk:
                result.append({"name": name, "description": rule.description})
        return result
