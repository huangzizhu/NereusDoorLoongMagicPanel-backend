"""
第三方 LLM 注入分类器。

用独立的 LLM 调用（复用 LLMProvider 体系，不自研模型）对不可信文本做
"是否包含提示词注入意图"的二分类。与正则快筛互补：正则覆盖已知话术，
分类器覆盖未知/混淆/多语言变体。

三种运行模式（injection_llm_mode）：
- off      — 关闭分类器（仅保留正则快筛 + 金丝雀）
- sampling — 随机概率抽检（injection_sampling_rate，默认 0.1），
             压低第三方调用的成本与敏感数据外泄面
- full     — 全部检测（延迟/成本最高）

安全约定：
- 分类器使用独立 Provider 实例，不参与主对话，不持有任何工具权限；
- 判别失败（超时/解析失败）默认 fail-open（不阻断），分类器不得成为 DoS 面；
- 判别 prompt 用 <text> 标签隔离输入，并要求只输出 JSON。
"""
from __future__ import annotations
import asyncio
import random
from dataclasses import dataclass
from typing import Any

from agent.llm_providers.base import LLMProvider
from agent.llm_structured import (
    MAX_STRUCTURED_ATTEMPTS,
    StructuredOutputError,
    callStructuredLLM,
    parseJsonObject,
)
from agent.prompt_loader import renderPrompt

VALID_MODES = {"off", "sampling", "full"}


@dataclass
class ClassifierVerdict:
    """分类器判定结果。checked=False 表示未检测（异常降级/模式关闭）。"""
    injection: bool = False
    confidence: float = 0.0
    reason: str = ""
    checked: bool = False
    error: str = ""


class InjectionClassifier:
    """基于第三方 LLM 的注入二分类器。"""

    def __init__(self, provider: LLMProvider | None,
                 mode: str = "sampling",
                 samplingRate: float = 0.1,
                 timeoutSeconds: float = 10.0):
        self._provider = provider
        self._mode = mode if mode in VALID_MODES else "sampling"
        self._samplingRate = max(0.0, min(1.0, samplingRate))
        self._timeoutSeconds = max(0.5, timeoutSeconds)
        self._rng = random.Random()

    @property
    def mode(self) -> str:
        return self._mode

    def shouldCheck(self) -> bool:
        """根据模式决定本次是否执行分类器检测。

        Returns:
            True = 本次需要检测
        """
        if self._provider is None or self._mode == "off":
            return False
        if self._mode == "full":
            return True
        # sampling：随机抽检
        return self._rng.random() < self._samplingRate

    async def classify(self, text: str) -> ClassifierVerdict:
        """对单段文本做注入判别。

        内部有超时与异常兜底：任何失败都返回 checked=False 的
        fail-open 结果，绝不因分类器故障阻断主流程。
        """
        if self._provider is None or self._mode == "off":
            return ClassifierVerdict()
        if not text or not text.strip():
            return ClassifierVerdict()

        prompt = renderPrompt(
            "safety/injection_classifier.txt", {"TEXT": text[:4000]}
        )
        messages = [{"role": "user", "content": prompt}]

        try:
            result = await callStructuredLLM(
                self._provider,
                messages,
                self._parseStructured,
                maxAttempts=MAX_STRUCTURED_ATTEMPTS,
                timeoutSeconds=self._timeoutSeconds,
            )
        except asyncio.TimeoutError:
            return ClassifierVerdict(error=f"classifier_timeout({self._timeoutSeconds}s)")
        except Exception as exc:  # noqa: BLE001 — 分类器故障不得外泄
            return ClassifierVerdict(error=f"classifier_error: {type(exc).__name__}")

        if result is None:
            return ClassifierVerdict(
                error=(
                    "classifier_parse_failed_"
                    f"after_{MAX_STRUCTURED_ATTEMPTS}_attempts"
                )
            )

        parsed = result.value

        return ClassifierVerdict(
            injection=bool(parsed.get("injection", False)),
            confidence=float(parsed.get("confidence", 0.0)),
            reason=str(parsed.get("reason", ""))[:200],
            checked=True,
        )

    @staticmethod
    def _parse(raw: str) -> dict[str, Any] | None:
        """解析分类器输出，保留给测试和兼容调用方的宽容入口。"""
        try:
            return InjectionClassifier._parseStructured(raw)
        except (StructuredOutputError, TypeError, ValueError):
            return None

    @staticmethod
    def _parseStructured(raw: str) -> dict[str, Any]:
        """严格校验分类器 JSON 的字段和类型。"""
        data = parseJsonObject(raw)

        injection = data.get("injection")
        if type(injection) is not bool:
            raise StructuredOutputError("injection 必须是 boolean")

        confidence = data.get("confidence")
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0.0 <= float(confidence) <= 1.0
        ):
            raise StructuredOutputError("confidence 必须是 0 到 1 之间的数字")

        reason = data.get("reason", "")
        if not isinstance(reason, str):
            raise StructuredOutputError("reason 必须是字符串")

        return {
            "injection": injection,
            "confidence": float(confidence),
            "reason": reason,
        }
