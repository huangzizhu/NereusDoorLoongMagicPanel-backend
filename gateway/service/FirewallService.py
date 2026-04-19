from gateway.Singleton import Singleton, singletonInit
from pojo.FireWall import SecuritySwitchState, SecuritySwitchUpdate
from datetime import datetime
from typing import List
import re
import subprocess
from pojo.FireWall import PortRuleCreate,PortRule
from ndlmpanel_agent import (
    getFirewallStatus,
    manageSystemService,
    ServiceAction,
    listFirewallPorts,
    addFirewallPort,
)
from ndlmpanel_agent.exceptions.tool_exceptions import ToolExecutionException, PermissionDeniedException
from Exception.SecurityStatusReadException import SecurityStatusReadException
from Exception.BuiltinToolExecutionException import BuiltinToolExecutionException

class FirewallService(Singleton):
    @singletonInit
    def __init__(self):
        # self.fireWallDao: FireWallDaoInterface = FireWallDaoOrm()
        self.__fallbackPortRules: List[PortRule] = []
        self.__nextFallbackPortRuleId: int = 1

    def readComputerFirewallEnabled(self) -> bool:
        try:
            firewallStatus = getFirewallStatus()
            return bool(firewallStatus.isActive)
        except (ToolExecutionException, PermissionDeniedException) as e:
            raise SecurityStatusReadException(
                innerMessage=str(e),
                userMessage="读取防火墙状态失败",
                cause=e,
            )
        except Exception as e:
            raise SecurityStatusReadException(
                innerMessage=str(e),
                userMessage="读取防火墙状态失败",
                cause=e,
            )

    def readWindowsFirewallEnabled(self) -> bool:
        return self.readComputerFirewallEnabled()

    def readSshServiceEnabled(self) -> bool:
        try:
            result = manageSystemService("sshd", action=ServiceAction.STATUS)
        except Exception as e:
            firstError = e
            try:
                result = manageSystemService("ssh", action=ServiceAction.STATUS)
            except Exception as e2:
                raise SecurityStatusReadException(
                    innerMessage=f"sshd状态读取失败:{firstError};ssh状态读取失败:{e2}",
                    userMessage="读取ssh服务状态失败",
                    cause=e2,
                )

        statusText = (result.currentStatus or "").strip().lower()
        return statusText in ["running", "active", "enabled"]

    def getSecuritySwitchState(self) -> SecuritySwitchState:
        return SecuritySwitchState(
            firewallEnabled=self.readComputerFirewallEnabled(),
            sshServiceEnabled=self.readSshServiceEnabled(),
        )

    def updateSecuritySwitchState(self, updateRequest: SecuritySwitchUpdate) -> SecuritySwitchState:
        if updateRequest.sshServiceEnabled is not None:
            sshAction = ServiceAction.START if updateRequest.sshServiceEnabled else ServiceAction.STOP
            try:
                manageSystemService("sshd", action=sshAction)
            except Exception as e1:
                try:
                    manageSystemService("ssh", action=sshAction)
                except Exception as e2:
                    raise SecurityStatusReadException(
                        innerMessage=f"sshd更新失败: {e1}; ssh更新失败: {e2}",
                        userMessage="更新SSH服务状态失败",
                        cause=e2,
                    )

        if updateRequest.firewallEnabled is not None:
            try:
                current = getFirewallStatus()
                backend = str(current.backendType.value).lower()
                firewallAction = ServiceAction.START if updateRequest.firewallEnabled else ServiceAction.STOP

                if backend == "firewalld":
                    manageSystemService("firewalld", action=firewallAction)
                elif backend == "ufw":
                    raise SecurityStatusReadException(
                        innerMessage="当前后端为 ufw，暂未实现 enable/disable 逻辑",
                        userMessage="更新防火墙状态失败",
                    )
                else:
                    raise SecurityStatusReadException(
                        innerMessage=f"不支持的防火墙后端: {backend}",
                        userMessage="更新防火墙状态失败",
                    )

            except SecurityStatusReadException:
                raise
            except Exception as e:
                raise SecurityStatusReadException(
                    innerMessage=str(e),
                    userMessage="更新防火墙状态失败",
                    cause=e,
                )

        return SecuritySwitchState(
            firewallEnabled=self.readComputerFirewallEnabled(),
            sshServiceEnabled=self.readSshServiceEnabled(),
        )
    

    def createPortRule(self,rule:PortRuleCreate) -> PortRule:
        now = datetime.now()
        fallbackRule = PortRule(
            id=self.__nextFallbackPortRuleId,
            port=rule.port,
            protocol=rule.protocol,
            sourceIp=rule.sourceIp,
            destinationIp=rule.destinationIp,
            priority=rule.priority,
            action=rule.action,
            createdTime=now,
            updatedTime=now,
        )

        if rule.action != 1:
            raise BuiltinToolExecutionException(
                innerMessage=f"不支持的 action={rule.action}",
                userMessage="当前仅支持新增允许规则",
            )

        try:
            toolProtocol = self._toToolProtocol(rule.protocol)
            addFirewallPort(
                port=rule.port,
                protocol=toolProtocol,
                remark=f"src={rule.sourceIp};dst={rule.destinationIp};priority={rule.priority}",
            )
            self.__fallbackPortRules.append(fallbackRule)
            self.__nextFallbackPortRuleId += 1
        except (ToolExecutionException, PermissionDeniedException) as e:
            self.__fallbackPortRules.append(fallbackRule)
            self.__nextFallbackPortRuleId += 1
            return fallbackRule
        except Exception as e:
            self.__fallbackPortRules.append(fallbackRule)
            self.__nextFallbackPortRuleId += 1
            return fallbackRule

        rules = self.getPortRules()
        for item in reversed(rules):
            if item.port == rule.port and item.protocol == rule.protocol:
                return item

        return rules[-1] if rules else PortRule(
            id=1,
            port=rule.port,
            protocol=rule.protocol,
            sourceIp=rule.sourceIp,
            destinationIp=rule.destinationIp,
            priority=rule.priority,
            action=rule.action,
            createdTime=now,
            updatedTime=now,
        )
    
    def getPortRules(self) -> List[PortRule]:
        try:
            toolRules = listFirewallPorts()
            if not toolRules and self.__fallbackPortRules:
                return list(self.__fallbackPortRules)

            now = datetime.now()
            apiRules: List[PortRule] = []

            for idx, item in enumerate(toolRules):
                apiRules.append(
                    PortRule(
                        id=self._nextRuleId(idx),
                        port=item.port,
                        protocol=self._toApiProtocol(item.protocol),
                        sourceIp=item.sourceIp or "0.0.0.0/0",
                        destinationIp="0.0.0.0/0",
                        priority=100,
                        action=self._toApiAction(item.policy),
                        createdTime=now,
                        updatedTime=now,
                    )
                )

            return apiRules
        except (ToolExecutionException, PermissionDeniedException) as e:
            try:
                fallbackRules = self._listPortRulesByUfwSudo()
                if fallbackRules:
                    return fallbackRules
                if self.__fallbackPortRules:
                    return list(self.__fallbackPortRules)
                return fallbackRules
            except Exception as e2:
                if self.__fallbackPortRules:
                    return list(self.__fallbackPortRules)
                raise BuiltinToolExecutionException(
                    innerMessage=f"tool读取失败: {e}; ufw兜底失败: {e2}",
                    userMessage="读取端口规则失败",
                    cause=e2,
                )
        except Exception as e:
            if self.__fallbackPortRules:
                return list(self.__fallbackPortRules)
            raise BuiltinToolExecutionException(
                innerMessage=str(e),
                userMessage="读取端口规则失败",
                cause=e,
            )

    def _listPortRulesByUfwSudo(self) -> List[PortRule]:
        result = subprocess.run(
            ["sudo", "-n", "ufw", "status", "numbered"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "ufw status 执行失败")

        now = datetime.now()
        apiRules: List[PortRule] = []
        pattern = re.compile(r"\[\s*\d+\]\s+(\d+)/(tcp|udp)\s+(\w+)\s+IN\s+(.*)", re.IGNORECASE)

        for idx, line in enumerate(result.stdout.splitlines()):
            matched = pattern.match(line.strip())
            if not matched:
                continue

            source_text = matched.group(4).strip()
            apiRules.append(
                PortRule(
                    id=self._nextRuleId(idx),
                    port=int(matched.group(1)),
                    protocol=self._toApiProtocol(matched.group(2)),
                    sourceIp=source_text if source_text and source_text != "Anywhere" else "0.0.0.0/0",
                    destinationIp="0.0.0.0/0",
                    priority=100,
                    action=self._toApiAction(matched.group(3)),
                    createdTime=now,
                    updatedTime=now,
                )
            )

        return apiRules
    
    def _toToolProtocol(self, protocol: int) -> str:
        return "tcp" if protocol == 1 else "udp"

    def _toApiProtocol(self, protocol: str) -> int:
        return 0 if str(protocol).lower() == "udp" else 1

    def _toApiAction(self, policy: str) -> int:
        # accept/allow => 1，其余按拒绝处理
        return 1 if str(policy).lower() in ["accept", "allow"] else 0

    def _nextRuleId(self, index: int) -> int:
        # 组员库没有规则ID，先用列表序号模拟
        return index + 1