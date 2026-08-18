# 系统提示词（System Prompt）构成与修改指南

> 更新日期：2026-08-18
> 适用范围：`agent/` 运行时组装的全部系统提示词内容

本文档描述 NDLM Agent 的**系统提示词由哪些部分组成、各自从哪来、如何修改**，避免在错误的位置改动导致不生效。

## 1. 分层构成总览

每次 LLM 调用前，`PromptBuilder.build()` + `AgentCore._injectModePrompt()` 组装出完整消息，其中 `role: system` 的消息按以下顺序产生：

```
[L1] 主提示词（conf/prompts/system/v1.2.0.txt）
   + 安全规则（conf/prompts/safety/rules_summary.txt）
   + 安全金丝雀指令段（conf/prompts/safety/canary.txt，运行时填入令牌）
[L2] 当前策略（policyProfile，当前未启用）
[动态] 模式提示词（conf/prompts/modes/*.txt，每次调用前注入）
[动态] 已批准的执行计划（plan 审批通过后注入）
```

## 2. 各部分详情

### 2.1 L1 主提示词（静态文件）

| 项 | 值 |
|---|---|
| 文件 | `conf/prompts/system/v1.2.0.txt` |
| 加载点 | `agent/integration/session.py`（硬编码路径，缺失时兜底为"你是一个智能运维助手。"） |
| 内容 | 角色（NDLM）、核心规则、工作区说明、特权操作说明（三通道提权）、定时任务能力 |
| 版本 | `v1.0.0`（旧）→ `v1.1.0`（旧）→ `v1.2.0`（当前生效） |

**修改方式**：直接编辑 `v1.2.0.txt`，重启后端生效。旧版本文件（`v1.0.0.txt` / `v1.1.0.txt`）仅作历史留存，不被代码引用。

### 2.2 L1 安全规则（静态文件）

| 项 | 值 |
|---|---|
| 文件 | `conf/prompts/safety/rules_summary.txt` |
| 注入 | `PromptBuilder.build()` 以 `## 安全规则` 小节追加到主提示词后，两者合成同一条 system 消息 |

内容为禁止行为清单与防注入特征话术。**注意**：安全边界的强保证不依赖此文本，而是 `RuleEngine`（执行层硬规则）+ 特权代理；此文件是提示词层面的约束，两者互补。

### 2.3 安全金丝雀指令段（动态注入）

| 项 | 值 |
|---|---|
| 来源 | `agent/safety/canary.py` 生成的部署级令牌（持久化 `runtime/canary.json`，权限 600） |
| 模板 | `conf/prompts/safety/canary.txt` |
| 注入 | `PromptBuilder.build()` 在 L1 末尾动态追加模板，并填入部署级令牌 |
| 轮换 | 输出侧检测到令牌泄露（`AgentCore`）后自动轮换，并写审计 `canary.leaked` + 告警 `alert_events` |

**不在 `v1.2.0.txt` 中**：令牌是运行时动态值，无法写死在静态文件。修改金丝雀指令措辞编辑 `conf/prompts/safety/canary.txt`。

### 2.4 模式提示词（动态注入）

| 项 | 值 |
|---|---|
| 定义 | `conf/prompts/modes/read_only.txt`、`plan.txt`、`agent.txt`、`break_glass.txt`、`executing.txt` |
| 模式 | `read_only` / `plan` / `agent` / `break_glass` / `executing` |
| 加载 | `agent/agent_router/router.py` 通过 `agent/prompt_loader.py` 加载 |
| 注入 | `AgentCore._injectModePrompt()` 在每次 LLM 调用前、最后一条 user 消息之前插入 |

修改模式行为措辞改此字典。模式门控的**硬规则**在 `RuleEngine`（`agent/safety/rule_engine.py`）。

### 2.5 已批准的执行计划（动态注入）

| 项 | 值 |
|---|---|
| 格式化 | `agent/agent_router/plan_schema.py` `formatPlanForPrompt()` |
| 注入 | `AgentCore._waitForPlanApproval()` 审批通过后追加 `## 已批准的执行计划` system 消息 |

### 2.6 L2 当前策略（预留）

`PromptBuilder.build()` 支持 `policyProfile` 参数生成第二条 system 消息，当前 `AgentCore` 调用未传，**未启用**。

### 2.7 其他外部提示词资源

运行时的辅助 LLM 调用和后台 Agent 也统一从 `conf/prompts/` 加载：

| 目录 | 用途 | 主要加载点 |
|---|---|---|
| `conf/prompts/automation/` | 定时任务、自动巡检及巡检报告模板 | `gateway/service/ScheduledTaskService.py`、`InspectionService.py` |
| `conf/prompts/audit/` | 命令/脚本安全审计及重试提示 | `gateway/service/audit_service.py` |
| `conf/prompts/safety/` | 金丝雀、注入分类器和安全规则 | `agent/agent_core/prompt_builder.py`、`agent/safety/llm_classifier.py` |
| `conf/prompts/auxiliary/` | 连通性测试、会话标题生成 | `AgentLlmProfileService.py`、`AgentBackgroundRunner.py` |
| `conf/prompts/legacy/` | 旧配置接口的兼容默认提示词 | `utils/toolFunction/config.py` |

经验库提示词位于 conf/prompts/knowledge/，由 OpsExperienceService 提供冷启动指引、
检索与沉淀规则；它与经验包实现代码一起部署，但不包含任何运行时导出的经验包数据。

工具 schema 中的简短描述仍属于工具元数据，位于
`ndlmpanel_agent/mcp/server/tool_adapter.py`；涉及安全决策的详细规则以本文件和
`conf/prompts/system/`、`conf/prompts/safety/` 为准。

## 3. 各 system 消息注入点速查

| 注入点 | 位置 |
|---|---|
| L1 主提示词 + 安全规则 + 金丝雀 | `agent/agent_core/prompt_builder.py` `build()` |
| 模式提示词 | `agent/agent_core/agent_loop.py` `_injectModePrompt()` |
| 已批准计划 / 审批超时 | `agent/agent_core/agent_loop.py` `_waitForPlanApproval()` |
| 对话历史摘要（压缩） | `agent/context_mgmt/compressor.py` |
| 定时任务 / 巡检引导 | `conf/prompts/automation/`，由 `gateway/service/` 注入 |

## 4. 修改流程建议

1. 修改主提示词 → 编辑 `conf/prompts/system/v1.2.0.txt` 或 `conf/prompts/safety/rules_summary.txt`；
2. 修改模式/金丝雀/无人值守措辞 → 编辑 `conf/prompts/modes/`、`conf/prompts/safety/` 或 `conf/prompts/automation/` 下对应文件；
3. `agent/prompt_loader.py` 只负责读取文件和替换显式占位符，代码中不要重新硬编码大段提示词；
4. 改动后跑 `tests/unit/test_injection_defense.py`（金丝雀相关）与 `tests/unit/test_mode_gating.py`（模式相关）；
5. 涉及 KV-Cache 优化注意：静态前缀（L1）应保持稳定，模式/计划等动态段插入位置在 user 消息之后，不影响前缀缓存。

## 5. 相关文档

- 注入防护组合拳设计：`docs/prompt-injection-defense.md`
- 安全规则与执行层门控：`agent/safety/rule_engine.py`、`conf/policies/`
