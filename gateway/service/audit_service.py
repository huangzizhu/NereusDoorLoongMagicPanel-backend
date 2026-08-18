"""AI-SAST 安全审计服务。

在管理员批准特权码之前，对命令/脚本进行 LLM 安全分析。
结果返回结构化 JSON，供 CLI 用 rich Markdown 渲染。
"""

import json
import logging
import urllib.error
import urllib.request

from typing import Any

from agent.llm_structured import (
    MAX_STRUCTURED_ATTEMPTS,
    StructuredOutputError,
    buildStructuredRetryPrompt,
    parseJsonObject,
)
from agent.prompt_loader import loadPrompt
from gateway.utils.llm_utils import get_llm_config as _get_llm_config_shared, normalize_endpoint as _normalize_endpoint_shared

logger = logging.getLogger("audit_service")

# ── LLM 审计系统提示词 ──
_SAST_SYSTEM_PROMPT = loadPrompt("audit/sast_system.txt")


def _get_default_llm_config() -> dict[str, str]:
    """从后端默认 profile 读取 LLM 配置（endpoint, api_key, model）。

    委托给共享的 get_llm_config()，保留 audit_service 的调试日志。
    """
    result = _get_llm_config_shared()
    if result.get("endpoint") and result.get("api_key"):
        ep = result["endpoint"]
        print(f"[AUDIT_DEBUG] 使用 LLM 配置: endpoint={ep[:50]}... model={result['model']}", flush=True)
    else:
        print("[AUDIT_DEBUG] ❌ get_llm_config() 未找到有效 LLM 配置", flush=True)
    return result


_MAX_RETRIES = MAX_STRUCTURED_ATTEMPTS


def _llm_chat(messages: list[dict], config_override: dict[str, str] | None = None) -> str | None:
    """调用 LLM API，传入完整消息列表（含 system 和对话历史）。

    Args:
        messages: OpenAI 格式的消息列表
        config_override: 可选的 LLM 配置覆盖

    Returns:
        LLM 响应文本（assistant content），或 None（调用失败）
    """
    llm_config = config_override or _get_default_llm_config()

    endpoint = llm_config.get("endpoint", "")
    api_key = llm_config.get("api_key", "")
    model = llm_config.get("model", "deepseek-chat")

    if not api_key or not endpoint:
        print("[AUDIT_DEBUG] ❌ LLM 配置不完整", flush=True)
        return None

    # 归一化 endpoint（复用共享 utils）
    endpoint = _normalize_endpoint_shared(endpoint)

    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2048,
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            result = json.loads(raw)
            choices = result.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                return content
            content = result.get("content", [])
            if content:
                return content[0].get("text", "")
            logger.warning("AI-SAST: LLM 返回格式异常: %s", str(result)[:200])
            return None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:200]
        logger.error("AI-SAST: LLM API HTTP %d: %s", e.code, err_body)
        return None
    except urllib.error.URLError as e:
        logger.error("AI-SAST: LLM API 连接失败: %s", e.reason)
        return None
    except json.JSONDecodeError as e:
        logger.error("AI-SAST: LLM 响应 JSON 解析失败: %s", e)
        return None
    except Exception as e:
        logger.exception("AI-SAST: LLM 调用异常: %s", e)
        return None


def _call_llm_with_retry(system_prompt: str, user_prompt: str) -> str | None:
    """调用 LLM 并自动重试，最多 _MAX_RETRIES 次。

    如果 LLM 返回的 JSON 解析失败，将错误消息 + 原始回复拼入 messages，
    让 LLM 修正后重试。
    """
    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for attempt in range(1, _MAX_RETRIES + 1):
        print(f"[AUDIT_DEBUG] LLM 调用 第{attempt}次", flush=True)

        content = _llm_chat(messages)
        if content is None:
            # 网络/配置错误，不重试
            return None

        print(f"[AUDIT_DEBUG] LLM 原始回复（前200字符）: {content[:200]}", flush=True)

        # 尝试解析 JSON
        parsed = _parse_llm_response(content)
        if parsed is not None:
            # 解析成功
            return content

        # 解析失败：构造修正消息
        error_msg = buildStructuredRetryPrompt(
            _last_parse_error,
            content,
            maxPreviousChars=1500,
        )

        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": error_msg})
        print(f"[AUDIT_DEBUG] ❌ 第{attempt}次 JSON 解析失败，已通知 LLM 修正", flush=True)

    print(f"[AUDIT_DEBUG] ❌ 已达最大重试次数 {_MAX_RETRIES}，放弃", flush=True)
    return None

_last_parse_error: str = ""


def _normalize_json(text: str) -> str:
    """修复 LLM 返回 JSON 中的常见格式问题。

    LLM 有时会输出全角符号（）、｛｝【】等），
    或末尾多一个逗号，或缺失引号。
    此函数做柔和修复后再尝试解析。
    """
    # 全角 → 半角
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("｛", "{").replace("｝", "}")
    text = text.replace("【", "[").replace("】", "]")
    text = text.replace("，", ",").replace("：", ":")
    text = text.replace("＂", '"').replace("＇", "'")
    # 移除末尾多余逗号（json 不允许 trailing comma）
    text = text.rstrip().rstrip(",")
    return text


def _parse_llm_response(response_text: str) -> dict[str, Any] | None:
    """从 LLM 响应中提取 JSON 审计报告。

    LLM 可能返回带 ```json ``` 围栏的文本，需要提取。
    也会自动修复全角符号等常见格式问题。

    解析失败时将错误原因记录到全局 _last_parse_error，供重试逻辑使用。
    """
    global _last_parse_error

    if not response_text:
        _last_parse_error = "响应内容为空"
        return None

    text = response_text.strip()

    # 尝试提取 ```json ... ``` 块
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start) if "```" in text[start:] else len(text)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start) if "```" in text[start:] else len(text)
        text = text[start:end].strip()

    # 先尝试直接解析，失败则做全角修复后重试。
    for idx, attempt in enumerate([text, _normalize_json(text)]):
        try:
            result = parseJsonObject(attempt)
        except (StructuredOutputError, TypeError, ValueError) as exc:
            _last_parse_error = f"第{idx + 1}次尝试: {exc}"
            continue

        try:
            _validate_audit_report(result)
        except StructuredOutputError as exc:
            _last_parse_error = f"第{idx + 1}次尝试: {exc}"
            continue
        return result

    # 两次都失败
    logger.warning("AI-SAST: LLM 响应非 JSON（前200字符: %s）", text[:200])
    # 这里必须返回 None，让上层重试；重试耗尽后的降级由
    # audit_commands/audit_script_content 的规则审计负责。
    return None


def _validate_audit_report(report: dict[str, Any]) -> None:
    """校验审计报告的完整结构和字段类型。

    只有 JSON 语法正确还不够：缺字段或字段类型错误同样要退回模型，
    否则下游会把半结构化内容当成可信审计结论。
    """
    required = {
        "risk_level",
        "summary",
        "findings",
        "dangerous_commands",
        "network_requests",
        "nested_execution",
        "ai_advice",
    }
    missing = sorted(required - report.keys())
    if missing:
        raise StructuredOutputError(f"缺少必填字段: {', '.join(missing)}")

    if report["risk_level"] not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise StructuredOutputError("risk_level 不是允许的值")
    if not isinstance(report["summary"], str) or not report["summary"].strip():
        raise StructuredOutputError("summary 必须是非空字符串")
    if type(report["network_requests"]) is not bool:
        raise StructuredOutputError("network_requests 必须是 boolean")
    if type(report["nested_execution"]) is not bool:
        raise StructuredOutputError("nested_execution 必须是 boolean")
    if not isinstance(report["ai_advice"], str):
        raise StructuredOutputError("ai_advice 必须是字符串")

    dangerous_commands = report["dangerous_commands"]
    if (
        not isinstance(dangerous_commands, list)
        or not all(isinstance(item, str) for item in dangerous_commands)
    ):
        raise StructuredOutputError("dangerous_commands 必须是字符串数组")

    findings = report["findings"]
    if not isinstance(findings, list):
        raise StructuredOutputError("findings 必须是数组")
    finding_fields = {
        "severity",
        "description",
        "code_snippet",
        "recommendation",
    }
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise StructuredOutputError(f"findings[{index}] 必须是对象")
        missing_fields = sorted(finding_fields - finding.keys())
        if missing_fields:
            raise StructuredOutputError(
                f"findings[{index}] 缺少必填字段: {', '.join(missing_fields)}"
            )
        if finding["severity"] not in {"danger", "warning", "info"}:
            raise StructuredOutputError(
                f"findings[{index}].severity 不是允许的值"
            )
        for field_name in ("description", "code_snippet", "recommendation"):
            if not isinstance(finding[field_name], str):
                raise StructuredOutputError(
                    f"findings[{index}].{field_name} 必须是字符串"
                )


def audit_commands(commands: list[dict[str, Any]]) -> dict[str, Any]:
    """审计一组特权命令/脚本。

    Args:
        commands: [{"command": "mkdir", "args": ["-p", "/var/www/test"]}, ...]

    Returns:
        结构化审计报告 dict（与 CLI _display_audit_report 兼容）
    """
    # 构建审计内容
    lines = []
    for i, cmd in enumerate(commands, 1):
        cmd_name = cmd.get("command", "?")
        cmd_args = " ".join(str(a) for a in cmd.get("args", []))
        lines.append(f"命令 {i}: {cmd_name} {cmd_args}")

    user_prompt = "\n".join(lines)
    response_text = _call_llm_with_retry(_SAST_SYSTEM_PROMPT, user_prompt)
    result = _parse_llm_response(response_text) if response_text else None

    if result is None:
        result = _rule_based_audit(commands)

    return result


def audit_script_content(script_content: str, script_path: str = "") -> dict[str, Any]:
    """审计脚本内容。

    Args:
        script_content: 脚本全文
        script_path: 脚本文件路径（仅用于日志）

    Returns:
        结构化审计报告 dict
    """
    user_prompt = (
        f"脚本路径: {script_path}\n"
        f"脚本内容:\n```bash\n{script_content}\n```"
    )
    response_text = _call_llm_with_retry(_SAST_SYSTEM_PROMPT, user_prompt)
    result = _parse_llm_response(response_text) if response_text else None

    if result is None:
        result = _rule_based_audit_script(script_content)

    return result


def _rule_based_audit(commands: list[dict]) -> dict[str, Any]:
    """基于规则的降级审计（LLM 不可用时的回退方案）。"""
    import re

    dangerous_found: list[str] = []
    findings: list[dict] = []
    has_network = False
    has_nested = False
    highest_risk = "LOW"

    dangerous_patterns = [
        (re.compile(r'\brm\s+-[rR]f\b'), "danger", "递归强制删除"),
        (re.compile(r'\bchmod\s+777\b'), "danger", "777 权限过于宽松"),
        (re.compile(r'\beval\b'), "danger", "eval 动态执行"),
        (re.compile(r'\bexec\b'), "danger", "exec 执行"),
        (re.compile(r'\bsource\s'), "warning", "source 加载外部脚本"),
        (re.compile(r'\bcurl\b'), "warning", "包含 curl 网络请求"),
        (re.compile(r'\bwget\b'), "warning", "包含 wget 网络请求"),
        (re.compile(r'\bnc\b'), "warning", "包含 nc 网络工具"),
        (re.compile(r'\biptables\s+-F\b'), "danger", "清空防火墙规则"),
        (re.compile(r'\bmkfs\.'), "danger", "格式化操作"),
    ]

    for cmd in commands:
        cmd_name = cmd.get("command", "")
        cmd_args = " ".join(str(a) for a in cmd.get("args", []))
        text = f"{cmd_name} {cmd_args}"

        for pat, severity, desc in dangerous_patterns:
            if pat.search(text):
                dangerous_found.append(text)
                findings.append({
                    "severity": severity,
                    "description": f"发现{desc}操作",
                    "code_snippet": text[:100],
                    "recommendation": "请确认是否必要",
                })
                if severity == "danger":
                    highest_risk = "HIGH"
                elif severity == "warning" and highest_risk == "LOW":
                    highest_risk = "MEDIUM"

        if any(kw in text for kw in ["curl", "wget", "nc"]):
            has_network = True
        if any(kw in text for kw in ["eval", "exec", "source"]):
            has_nested = True

    return {
        "risk_level": highest_risk,
        "summary": f"共 {len(commands)} 个操作，规则扫描完成",
        "findings": findings,
        "dangerous_commands": dangerous_found,
        "network_requests": has_network,
        "nested_execution": has_nested,
        "ai_advice": "LLM 审计不可用，以上为规则扫描结果",
    }


def _rule_based_audit_script(content: str) -> dict[str, Any]:
    """基于规则的脚本降级审计。"""
    import re

    findings: list[dict] = []
    dangerous_commands: list[str] = []
    has_network = False
    has_nested = False
    highest_risk = "LOW"

    checks = [
        (re.compile(r'\beval\b'), "danger", "eval 动态执行", True),
        (re.compile(r'\bexec\s+'), "danger", "exec 替换进程", True),
        (re.compile(r'\bsource\s+'), "danger", "source 加载外部脚本", True),
        (re.compile(r'\.\s+/'), "warning", ". 点号加载外部文件", True),
        (re.compile(r'\bcurl\b'), "warning", "curl 网络请求", False),
        (re.compile(r'\bwget\b'), "warning", "wget 网络请求", False),
        (re.compile(r'\bnc\b'), "warning", "nc 网络工具", False),
        (re.compile(r'\|\s*(ba|z|k)?sh\b'), "danger", "管道直接执行", True),
        (re.compile(r'\bchmod\s+777\b'), "danger", "777 权限", False),
        (re.compile(r'\biptables\s+-F\b'), "danger", "清空防火墙", False),
    ]

    for pat, severity, desc, is_nested in checks:
        matches = pat.findall(content)
        if matches:
            dangerous_commands.append(desc)
            findings.append({
                "severity": severity,
                "description": f"脚本包含{desc}",
                "code_snippet": desc,
                "recommendation": "Trojan Horse 风险，建议拒绝",
            })
            if is_nested:
                has_nested = True
            if severity == "danger":
                highest_risk = "HIGH"

    if any(pat.search(content) for pat in [re.compile(r'\bcurl\b'), re.compile(r'\bwget\b'), re.compile(r'\bnc\b')]):
        has_network = True

    if not findings:
        highest_risk = "LOW"

    return {
        "risk_level": highest_risk,
        "summary": f"脚本规则扫描完成，共 {len(findings)} 个发现项",
        "findings": findings,
        "dangerous_commands": dangerous_commands,
        "network_requests": has_network,
        "nested_execution": has_nested,
        "ai_advice": "LLM 审计不可用，以上为规则扫描结果",
    }
