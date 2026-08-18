# 提示词注入防护（组合拳）设计文档

> 更新日期：2026-08-11
> 涉及模块：`agent/safety/`、`agent/agent_core/`、`agent/integration/`、`agent/config_envs/`

## 1. 背景与威胁模型

本项目原防护仅有一层：`agent/safety/injection_detector.py` 的 13 条正则，且在**用户消息入口**单点检测。两个明显短板：

1. **正则极易绕过**：大小写、插入空白/标点、Unicode 同形字、拆词、多语言、Base64/emoji 编码等混淆手段都能绕过（OWASP LLM01:2025 攻击场景 #9 Multilingual/Obfuscated Attack）。
2. **完全不防间接注入（Indirect Prompt Injection）**：`readFile` 读到的文件内容、网页内容、MCP 工具返回值会**原样拼接进对话上下文**，其中夹带的指令会被模型当作系统指令执行（OWASP 场景 #2/#4）。对会读文件、执行命令的运维 Agent，这是最危险的敞口。

参照 [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) 的 7 条缓解策略，本项目原有第 4/5 条（最小权限、人工审批）已由 RuleEngine + 特权代理实现，本次补齐第 3/6 条并加强第 1 条。

## 2. 组合拳架构总览

```
用户消息 ──► [正则快筛] ──► [LLM 分类器抽检] ──► Agent 循环
                    │ 命中即拒                    │
                    ▼                             ▼
            system prompt（含金丝雀令牌） ◄── PromptBuilder
                    │
                    ▼
              LLM 响应（文本 + 工具参数）
                    │
                    ▼
         [金丝雀输出侧检测] ──命中──► 拦截本轮 + 告警 + 轮换令牌
                    │ 未命中
                    ▼
            工具执行 ──► [工具输出过滤：正则 + 分类器] ──► 回传模型
                              │ 命中：替换为警示文本（原始输出入审计）
                              ▼
                     RuleEngine / 审批（既有执行层硬规则）
```

| 层 | 作用 | 防什么 |
|---|---|---|
| 正则快筛 | 用户入口低延迟首筛 | 已知话术（直接注入） |
| LLM 分类器 | 未知/混淆/多语言变体兜底 | 直接 + 间接注入 |
| 金丝雀令牌 | 输出侧信号 + system prompt 泄露检测 | 未知攻击、提示词泄露 |
| 工具输出过滤 | 外部数据隔离 | 间接注入 |
| RuleEngine + 审批（既有） | 执行层硬边界 | 注入成功后的危害 |

## 3. 实现细节

### 3.1 金丝雀令牌（Canary Token）

**文件**：`agent/safety/canary.py`

- **令牌**：`NDLM-CANARY-<32位hex>`，部署级生成并持久化到 `runtime/canary.json`。
- **注入**：`PromptBuilder.build()` 在 L1 system 消息末尾追加「安全金丝雀」段，明文包含当前令牌，并指示模型：任何输入要求复述/泄露该令牌 → 判定为注入，停止并拒绝。
- **输出侧检测**：`AgentCore` 每次 LLM 响应重建后，对 `content` + 全部 `tool_calls` 的 `arguments` 做 `token in text` 匹配。命中 → 写入审计 `canary.leaked` → **轮换令牌** → 发送 ERROR 事件并中止本轮（不执行任何工具调用）。
- **为什么有效**：模型知道令牌值、攻击者不知道。攻击者伪造的「复述指令」永远无法正确引用该值，一旦模型被诱导输出令牌即暴露注入；程序在输出侧即可判定，不依赖模型自觉。

**与 KV-Cache 的关系**：令牌**部署级固定**（只在泄露后轮换），`runtime/canary.json` 跨进程复用，因此 system prompt 前缀稳定，前缀缓存命中不受影响。轮换是罕见事件，代价可接受。

### 3.2 第三方 LLM 注入分类器

**文件**：`agent/safety/llm_classifier.py`

- 复用现有 `LLMProvider` 体系（`createProvider`）创建一个**独立** provider 实例做二分类，不参与主对话、不持有工具权限。
- 判别 prompt 用 `<text>` 标签隔离输入并要求只输出 JSON：`{"injection": bool, "confidence": 0-1, "reason": "..."}`。
- 三种模式（配置 `injection_llm_mode`）：
  - `off`：关闭（仅保留正则 + 金丝雀）
  - `sampling`：随机抽检（`injection_sampling_rate`，默认 0.1），压低第三方调用的成本与敏感数据外泄面
  - `full`：全检测（延迟/成本最高，适合严格环境）
- **fail-open 约定**：分类器超时/解析失败/异常一律返回「未检测」结果，**绝不阻断主流程**——分类器不得成为 DoS 面。

**数据出本地提示**：`full` 模式下工具输出会发给第三方 LLM API 判别，若输出含服务器敏感信息，建议使用 `sampling` 或自托管模型。

### 3.3 工具输出过滤（间接注入防线）

**位置**：`AgentCore._appendToolMessage()`（`agent/agent_core/agent_loop.py`）

所有工具输出在进入对话上下文前统一经过：
1. **正则快筛**：命中直接替换为警示文本；
2. **分类器抽检**（按 `injection_llm_mode`）：判定注入则替换。

被过滤的原始输出（前 200 字符）写入审计 `tool_output.injection`，便于事后核对、降低误报影响。良性输出原样透传。

### 3.4 用户输入检测

`AgentCore._runLoop` 入口：正则快筛（既有）→ 分类器抽检（新增，`shouldCheck()` 命中才调用 `classify()`），任一命中即发 `injection.detected` 审计并拒绝。

## 4. 配置说明

`AgentConfig` 新增字段（`agent/shared/types.py`）：

| 字段 | 默认值 | 说明 |
|---|---|---|
| `canary_enabled` | `true` | 金丝雀总开关 |
| `injection_llm_mode` | `sampling` | `off` / `sampling` / `full` |
| `injection_sampling_rate` | `0.1` | 抽检概率 0.0-1.0 |

JSON 配置示例：

```json
{
  "canary_enabled": true,
  "injection_llm_mode": "full",
  "injection_sampling_rate": 0.1
}
```

环境变量（`NDLM_` 前缀）：`NDLM_CANARY_ENABLED`、`NDLM_INJECTION_LLM_MODE`、`NDLM_INJECTION_SAMPLING_RATE`。

## 5. 审计与告警

### 5.1 trace 审计事件

| 事件 | 触发点 | 载荷 |
|---|---|---|
| `injection.detected` | 用户输入被正则/分类器拦截 | `source`(regex/classifier)、`confidence`、`reason` |
| `canary.leaked` | 模型输出泄露金丝雀令牌 | `round`、`content_len`、`tool_calls` 数 |
| `tool_output.injection` | 工具输出被过滤 | `source`、`confidence`、`reason`、`sample` |

可通过既有 trace 查询接口检索，用于事后审计与红队回归。

### 5.2 alert_events 告警联动

安全事件除写 trace 外，还通过 `AgentCore._emitAlert()` → `alertSink` 写入 `alert_events` 表（前端 `/system/alerts/*` 接口可见）：

| 事件 | level | message 摘要 |
|---|---|---|
| 金丝雀令牌泄露 | 2 (Error) | 检测到系统提示词泄露，已拦截并轮换令牌 |
| 用户输入被 LLM 分类器判定注入 | 2 (Error) | 含置信度与理由 |
| 用户输入命中正则快筛 | 1 (Warning) | 检测到注入特征已拒绝 |
| 工具输出被过滤 | 1 (Warning) | 正则或分类器命中 |

写入链路：`gateway/dao/SystemInfoDao.createAlert()`（新增），由 `agent/integration/session.py` 的 `_writeAgentAlert` 延迟注入，告警写入失败不影响 Agent 主流程。

> **告警内容安全约定**：写入 `alert_events` 的 `message` 为受控固定文本（不含第三方 LLM 生成的 `reason` 原文，避免敏感数据入库）；前端展示告警时应按不可信数据处理（HTML 转义），防止存储型 XSS。

## 6. 测试

`tests/unit/test_injection_defense.py`（23 个用例）：

- CanaryManager：生成格式 / 跨实例持久化 / 轮换 / 泄露检测 / 禁用降级
- InjectionClassifier：三模式决策 / JSON 与 markdown 解析 / 解析失败与异常 fail-open / 无 provider 降级
- PromptBuilder：金丝雀注入 system prompt / 轮换后使用新令牌
- AgentCore 集成：金丝雀泄露→ERROR+轮换且不执行工具 / 正常回复不误拦 / 工具输出正则与分类器过滤 / 良性输出透传 / 用户输入分类拦截与放行

## 7. 已知限制与后续建议

- **金丝雀不是绝对防御**：模型仍可能被更复杂的手段诱导（如要求"翻译"或"编码"后再输出），程序侧字符串匹配无法覆盖编码变体。建议后续对泄露文本做规范化（去空白/解码）后再匹配。
- **金丝雀只检测、不阻止泄露**：流式输出下 TEXT_DELTA 会先逐 token 推送给前端，输出侧检测在其后执行；令牌泄露时内容已实时送达。令牌本身无授权价值（仅审计信号），检测的意义在于告警 + 轮换，阻断动作由后续审批/RuleEngine 承担。
- **分类器召回率有限**：分类器与主对话复用同一模型/配置（`session.py` 中两次 `createProvider(config)`），对抗注入能力与主模型相当，可能被诱导漏检（输出 `injection:false`）或全量误报（可用性 DoS）。建议：默认 `sampling` 压低暴露面；严格环境改用独立/更强模型或本地微调小模型（数据不出本地）；定期用公开注入数据集（`deepset/prompt-injections`、GAP、HADES）做红队回归。
- **敏感数据出本地**：`full` 模式下工具输出原文（前 4000 字符）会发给第三方 LLM 判别；`sampling` 模式按概率降低暴露面。工具输出若含内网文件/密钥，请评估使用 `off` + 仅金丝雀，或改自托管模型。
- **输出侧全面检测**：目前仅检测金丝雀泄露；可进一步对模型输出做敏感信息（system prompt 原文、密钥）正则检测。
- **指令层级**：建议在系统提示词中显式声明 `system > user > tool data` 优先级，与工具输出隔离标签配合（本期已含金丝雀指示，标签化可作下一步）。
