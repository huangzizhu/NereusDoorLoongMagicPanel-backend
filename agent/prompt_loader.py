"""从项目配置目录加载和渲染提示词资源。"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ProjectRoot import getProjectRootPath


PROMPT_ROOT = getProjectRootPath() / "conf" / "prompts"


def _resolvePromptPath(relativePath: str) -> Path:
    """解析提示词资源路径，并拒绝越出 ``conf/prompts`` 的路径。"""
    if not isinstance(relativePath, str) or not relativePath.strip():
        raise ValueError("relativePath must be a non-empty string")

    root = PROMPT_ROOT.resolve()
    path = (root / relativePath).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"prompt path must stay under {root}: {relativePath!r}"
        ) from exc
    return path


def loadPrompt(relativePath: str, *, fallback: str | None = None) -> str:
    """加载一个项目内提示词文件。

    ``relativePath`` 只能指向固定的 ``conf/prompts`` 子路径；调用方不应
    将用户输入拼接到路径中。默认严格报错，只有明确传入 fallback 时才降级。
    """
    path = _resolvePromptPath(relativePath)
    try:
        return path.read_text(encoding="utf-8").rstrip()
    except FileNotFoundError:
        if fallback is not None:
            return fallback
        raise


def renderPrompt(
    relativePath: str,
    replacements: Mapping[str, object] | None = None,
    *,
    fallback: str | None = None,
) -> str:
    """加载提示词并替换 ``{{NAME}}`` 占位符。

    使用显式占位符替换而不是 ``str.format``，避免提示词中的 JSON、shell
    和代码示例被误当成格式化表达式。
    """
    content = loadPrompt(relativePath, fallback=fallback)
    for key, value in (replacements or {}).items():
        content = content.replace("{{" + key + "}}", str(value))
    return content
