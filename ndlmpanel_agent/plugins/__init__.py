"""
运维工具插件 — 纯 stdlib 实现。

每个子模块通过 TOOLS dict 声明提供的工具及其风险等级。
ToolRegistry.registerModule(module) 会自动发现并注册。

新增插件只需：
  1. 创建 plugins/xxx.py，导出 TOOLS = {"funcName": ToolRiskLevel.XXX, ...}
  2. 函数参数使用类型注解（schemas.py 自动生成 JSON Schema）
  3. 在 _ALL_MODULES 列表中添加模块引用
"""
from ndlmpanel_agent.plugins import (
    observation, process, network, service, filesystem,
)

# 所有需要自动注册的插件模块
_ALL_MODULES = (observation, process, network, service, filesystem)


def registerAll(registry) -> int:
    """一次性自动注册全部插件模块。

    Args:
        registry: ToolRegistry 实例

    Returns:
        成功注册的工具总数
    """
    total = 0
    for mod in _ALL_MODULES:
        total += registry.registerModule(mod)
    return total
