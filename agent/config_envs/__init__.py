"""
Config 配置系统 — JSON 加载、多级合并、密钥管理。
零外部依赖，基于 Python 3.10+ stdlib json + dataclasses。
"""
from agent.config_envs.loader import loadConfig, mergeConfigs
from agent.config_envs.secrets import getSecret
from agent.config_envs.schema import validateConfig
__all__ = ["loadConfig", "mergeConfigs", "getSecret", "validateConfig"]
