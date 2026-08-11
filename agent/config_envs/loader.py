"""
配置加载器。
合并优先级：内置默认 → JSON 文件 → NDLM_* 环境变量 → 运行时 overrides
"""
from __future__ import annotations
import json, os
from copy import deepcopy
from typing import Any
from agent.config_envs.secrets import getSecret
from agent.config_envs.dotenv import loadDotenv
from agent.shared.errors import AgentError, ErrorCode
from agent.shared.types import AgentConfig

_BUILTIN: dict[str, Any] = {
    "llm_provider": "deepseek",
    "llm_endpoint": "", "llm_model": "deepseek-v4-pro",
    "llm_max_tokens": 65536, "llm_context_window": 1048576, "safety_policy": "default",
    "execution_user": "osagent",
    "trace_db_path": os.path.join("runtime", "sqlite", "traces.db"),
    "max_tool_rounds": 0, "tool_timeout_seconds": 60,
    "max_tool_calls_per_round": 0,
    "workspace_dir": "",
    "llm_temperature": 0.1, "llm_retry_count": 3, "llm_retry_delay": 2.0,
    # ── 提示词注入防护 ──
    "canary_enabled": True,
    "injection_llm_mode": "sampling",
    "injection_sampling_rate": 0.1,
}

_ENV_MAP = {
    "LLM_PROVIDER": "llm_provider",
    "LLM_ENDPOINT": "llm_endpoint", "LLM_MODEL": "llm_model",
    "LLM_MAX_TOKENS": "llm_max_tokens", "LLM_CONTEXT_WINDOW": "llm_context_window", "SAFETY_POLICY": "safety_policy",
    "EXECUTION_USER": "execution_user", "TRACE_DB_PATH": "trace_db_path",
    "MAX_TOOL_ROUNDS": "max_tool_rounds",
    "MAX_TOOL_CALLS_PER_ROUND": "max_tool_calls_per_round",
    "TOOL_TIMEOUT_SECONDS": "tool_timeout_seconds",
    "LLM_TEMPERATURE": "llm_temperature",
    "LLM_RETRY_COUNT": "llm_retry_count",
    "LLM_RETRY_DELAY": "llm_retry_delay",
    "CANARY_ENABLED": "canary_enabled",
    "INJECTION_LLM_MODE": "injection_llm_mode",
    "INJECTION_SAMPLING_RATE": "injection_sampling_rate",
}

_INT_FIELDS = {"llm_max_tokens", "llm_context_window", "max_tool_rounds", "max_tool_calls_per_round", "tool_timeout_seconds",
               "llm_retry_count"}
_FLOAT_FIELDS = {"llm_temperature", "llm_retry_delay", "injection_sampling_rate"}
_BOOL_FIELDS = {"canary_enabled"}
_AGENT_FIELDS = set(AgentConfig.__dataclass_fields__.keys())


def mergeConfigs(*configs: dict[str, Any]) -> dict[str, Any]:
    """深度合并，后面的覆盖前面的。"""
    result: dict[str, Any] = {}
    for cfg in configs:
        _deepMerge(result, cfg)
    return result


def loadConfig(path: str | None = None,
               overrides: dict[str, Any] | None = None,
               envFile: str | None = ".env") -> AgentConfig:
    """加载配置 → AgentConfig。llm_api_key 从环境变量注入。

    加载顺序：
      1. 若 envFile 存在，先加载 .env 注入 os.environ（不覆盖已有环境变量）
      2. 内置默认 → JSON 文件 → NDLM_* 环境变量 → 运行时 overrides
      3. 从环境变量注入 llm_api_key

    Args:
        path: JSON 配置文件路径
        overrides: 运行时覆盖（最高优先级）
        envFile: .env 文件路径；传 None 跳过 .env 加载
    """
    if envFile:
        loadDotenv(envFile, override=False)

    merged = deepcopy(_BUILTIN)

    if path is not None:
        try:
            with open(path, encoding="utf-8") as f:
                merged = mergeConfigs(merged, json.load(f))
        except FileNotFoundError:
            raise AgentError(ErrorCode.CONFIG_LOAD_FAILED,
                             f"配置文件不存在: {path}")
        except json.JSONDecodeError as exc:
            raise AgentError(ErrorCode.CONFIG_LOAD_FAILED,
                             f"JSON 格式错误: {exc}")

    merged = mergeConfigs(merged, _loadEnvOverrides())
    if overrides:
        merged = mergeConfigs(merged, overrides)

    try:
        config = AgentConfig(**{k: v for k, v in merged.items()
                                if k in _AGENT_FIELDS})
    except (TypeError, ValueError) as exc:
        raise AgentError(ErrorCode.CONFIG_INVALID,
                         f"配置校验失败: {exc}") from exc

    apiKey = getSecret("llm_api_key", "NDLM_LLM_API_KEY")
    if apiKey:
        config.llm_api_key = apiKey
    return config


def _deepMerge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deepMerge(base[k], v)
        else:
            base[k] = v


def _loadEnvOverrides() -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for envSuf, cfgKey in _ENV_MAP.items():
        val = os.environ.get(f"NDLM_{envSuf}")
        if val is not None:
            if cfgKey in _INT_FIELDS:
                try: val = int(val)
                except ValueError: continue
            elif cfgKey in _FLOAT_FIELDS:
                try: val = float(val)
                except ValueError: continue
            elif cfgKey in _BOOL_FIELDS:
                val = str(val).strip().lower() in ("1", "true", "yes", "on")
            overrides[cfgKey] = val
    return overrides


def loadMcpServersFromProject() -> list[dict] | None:
    """从 pyproject.toml 读取 [tool.ndlmpanel-agent.mcp-servers] 配置。

    pyproject.toml 格式示例：
        [tool.ndlmpanel-agent.mcp-servers.ndlmpanel-mcp]
        command = ["python", "-m", "ndlmpanel_agent.mcp"]

        [tool.ndlmpanel-agent.mcp-servers.agent-core-mcp]
        command = ["python", "-m", "agent.agent_mcp"]

    Returns:
        list[McpServerSpec-style dict]: name, command, cwd(可选)
        None: pyproject.toml 不存在或没有该配置
    """
    try:
        import tomllib
    except ImportError:
        return None

    from ProjectRoot import getProjectRootPath

    pyproject = getProjectRootPath() / "pyproject.toml"
    if not pyproject.exists():
        return None

    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return None

    servers = data.get("tool", {}).get("ndlmpanel-agent", {}).get("mcp-servers", {})
    if not isinstance(servers, dict) or not servers:
        return None

    result: list[dict] = []
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            continue
        command = spec.get("command")
        if not isinstance(command, list) or not command:
            continue
        entry: dict = {"name": name, "command": list(command)}
        cwd = spec.get("cwd")
        if isinstance(cwd, str) and cwd.strip():
            entry["cwd"] = cwd.strip()
        result.append(entry)

    return result if result else None


def loadWorkspaceDirFromProject() -> str:
    """从 pyproject.toml 读取 [tool.ndlmpanel-agent].workspace_dir。

    Returns:
        workspace_dir 字符串，未配置时返回 ""。
    """
    try:
        import tomllib
    except ImportError:
        return ""

    from ProjectRoot import getProjectRootPath

    pyproject = getProjectRootPath() / "pyproject.toml"
    if not pyproject.exists():
        return ""

    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return ""

    return data.get("tool", {}).get("ndlmpanel-agent", {}).get("workspace_dir", "") or ""
