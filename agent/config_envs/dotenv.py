"""
极简 .env 文件加载器 — 纯标准库，零依赖。

替代 python-dotenv，仅覆盖运维 Agent 所需的最小语义：
- `KEY=VALUE` 逐行解析
- 支持 `export KEY=VALUE` 前缀（兼容 shell 习惯）
- 支持 `#` 整行注释与行尾注释（引号内的 # 不算注释）
- 支持单/双引号包裹的值（去引号，双引号内解析 \\n \\t 转义）
- 空行与无效行静默跳过
- 默认不覆盖已存在的环境变量（override=False），
  保证显式设置的 shell 环境变量优先级高于 .env 文件

安全约定：.env 用于本地开发存放 API Key 等敏感配置，必须加入
.gitignore；生产环境应使用 systemd EnvironmentFile= 或进程环境变量。
"""
from __future__ import annotations

import os


def parseEnvFile(path: str) -> dict[str, str]:
    """解析 .env 文件为 dict，不写入环境。文件不存在时返回空 dict。"""
    result: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return result
    except OSError:
        return result

    for raw in lines:
        parsed = _parseLine(raw)
        if parsed is not None:
            key, value = parsed
            result[key] = value
    return result


def loadDotenv(path: str = ".env", override: bool = False) -> dict[str, str]:
    """加载 .env 并注入 os.environ。

    Args:
        path: .env 文件路径
        override: True 时覆盖已存在的环境变量；默认 False（环境变量优先）

    Returns:
        实际注入（或将注入）的键值对
    """
    parsed = parseEnvFile(path)
    for key, value in parsed.items():
        if override or key not in os.environ:
            os.environ[key] = value
    return parsed


def _parseLine(raw: str) -> tuple[str, str] | None:
    """解析单行，返回 (key, value) 或 None（空行/注释/非法行）。"""
    line = raw.strip()
    if not line or line.startswith("#"):
        return None

    if line.startswith("export "):
        line = line[len("export "):].lstrip()

    if "=" not in line:
        return None

    key, _, rawValue = line.partition("=")
    key = key.strip()
    if not key or not _isValidKey(key):
        return None

    value = _parseValue(rawValue.strip())
    return key, value


def _isValidKey(key: str) -> bool:
    """环境变量名：字母/数字/下划线，且不以数字开头。"""
    if not key or key[0].isdigit():
        return False
    return all(c.isalnum() or c == "_" for c in key)


def _parseValue(rawValue: str) -> str:
    """处理引号包裹与行尾注释。"""
    if not rawValue:
        return ""

    quote = rawValue[0]
    if quote in ('"', "'"):
        # 找到匹配的闭合引号
        end = rawValue.find(quote, 1)
        if end != -1:
            inner = rawValue[1:end]
            if quote == '"':
                # 双引号内处理常见转义
                inner = inner.replace("\\n", "\n").replace(
                    "\\t", "\t").replace('\\"', '"')
            return inner
        # 未闭合引号：当作普通值，去掉首引号
        return rawValue[1:]

    # 无引号：去掉行尾注释（# 前需有空白或在行首）
    hashPos = rawValue.find("#")
    if hashPos != -1:
        rawValue = rawValue[:hashPos].rstrip()
    return rawValue
