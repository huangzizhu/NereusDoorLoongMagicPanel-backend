from gateway.Singleton import Singleton, singletonInit
from pojo.FireWall import SecuritySwitchState, SecuritySwitchUpdate
from datetime import datetime
from typing import List
import re
import subprocess
from pojo.FireWall import PortRuleCreate,PortRule, SshConfig,SshConfigUpdate, SshLog
from pathlib import Path
from utils.toolFunction import (
    manageSystemService,
    ServiceAction,
)
from utils.toolFunction.exceptions.tool_exceptions import ToolExecutionException, PermissionDeniedException
from Exception.SecurityStatusReadException import SecurityStatusReadException
from Exception.BuiltinToolExecutionException import BuiltinToolExecutionException
from Exception.ExecutePermissionDeniedException import ExecutePermissionDeniedException
from gateway.service.PrivilegedAgentClient import PrivilegedAgentClient, PrivilegedAgentRemoteError
from privileged_agent.models import PrivilegedAction


#测试
class FirewallService(Singleton):
    @singletonInit
    def __init__(self):
        # self.fireWallDao: FireWallDaoInterface = FireWallDaoOrm()
        self.__fallbackPortRules: List[PortRule] = []
        self.__nextFallbackPortRuleId: int = 1
        self.privilegedAgentClient = PrivilegedAgentClient()

    def _agentContext(self):
        return self.privilegedAgentClient.defaultContext("gateway.firewall")

    def _callPrivilegedAgent(self, action: PrivilegedAction, payload: dict, userMessage: str):
        try:
            return self.privilegedAgentClient.call(action, payload, self._agentContext())
        except PrivilegedAgentRemoteError as e:
            if e.code in ["PERMISSION_DENIED", "PROXY_PERMISSION_DENIED"]:
                raise ExecutePermissionDeniedException(
                    innerMessage=e.details or e.message,
                    userMessage=userMessage,
                    cause=e,
                )
            raise BuiltinToolExecutionException(
                innerMessage=e.details or e.message,
                userMessage=userMessage,
                cause=e,
            )

    def _innerMessage(self, error: Exception) -> str:
        return getattr(error, "innerMessage", None) or str(error)

    def readComputerFirewallEnabled(self) -> bool:
        try:
            firewallStatus = self._callPrivilegedAgent(
                PrivilegedAction.FIREWALL_GET_STATUS,
                {},
                "读取防火墙状态失败",
            )
            return bool(firewallStatus["isActive"])
        except ExecutePermissionDeniedException as e:
            raise SecurityStatusReadException(
                innerMessage=e.innerMessage,
                userMessage="读取防火墙状态失败",
                cause=e,
            )
        except BuiltinToolExecutionException as e:
            raise SecurityStatusReadException(
                innerMessage=e.innerMessage,
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

    def getSshConfig(self) -> SshConfig:
        # 先读取主配置文件，不存在时再尝试通配目录
        mainConfigPath = Path("/etc/ssh/sshd_config")
        configFiles: List[Path] = []

        if mainConfigPath.exists():
            configFiles.append(mainConfigPath)
            parsed = self._parseSshConfigFiles(configFiles)
            includeGlobs = parsed.get("include", [])

            for pattern in includeGlobs:
                for matchedPath in Path("/").glob(pattern.lstrip("/")):
                    if matchedPath.is_file():
                        configFiles.append(matchedPath)
        else:
            fallbackDir = Path("/etc/ssh/sshd_config.d")
            if fallbackDir.exists() and fallbackDir.is_dir():
                configFiles.extend(sorted(fallbackDir.glob("*.conf")))



        if not configFiles:
            raise SecurityStatusReadException(
                innerMessage="未找到 sshd 配置文件",
                userMessage="读取SSH配置失败",
            ) 

        try:
            parsed = self._parseSshConfigFiles(configFiles)

            sshPort = self._safeInt(parsed.get("port", ["22"])[-1], default=22)
            permitRootLogin = parsed.get("permitrootlogin", ["no"])[-1]
            passwordAuthentication = parsed.get("passwordauthentication", ["yes"])[-1]
            allowUsers = parsed.get("allowusers", [])
            allowGroups = parsed.get("allowgroups", [])
            listenAddress = parsed.get("listenaddress", ["0.0.0.0"])
            protocol = self._safeInt(parsed.get("protocol", ["2"])[-1], default=2)
            loginGraceTime = self._parseDurationToSeconds(parsed.get("logingracetime", ["120"])[-1], default=120)
            maxAuthTries = self._safeInt(parsed.get("maxauthtries", ["6"])[-1], default=6)

            statSource = configFiles[0]
            fileStat = statSource.stat()
            updatedTime = datetime.fromtimestamp(fileStat.st_mtime)
            createdTime = datetime.fromtimestamp(fileStat.st_ctime)

            return SshConfig(
                id=1,
                port=sshPort,
                permitRootLogin=permitRootLogin,
                passwordAuthentication=passwordAuthentication,
                allowUsers=allowUsers,
                allowGroups=allowGroups,
                listenAddress=listenAddress,
                protocol=protocol,
                loginGraceTime=loginGraceTime,
                maxAuthTries=maxAuthTries,
                createdTime=createdTime,
                updatedTime=updatedTime,
            )
        except SecurityStatusReadException:
            raise
        except PermissionError as e:
            raise SecurityStatusReadException(
                innerMessage=str(e),
                userMessage="读取SSH配置失败",
                cause=e,
            )
        except Exception as e:
            raise SecurityStatusReadException(
                innerMessage=str(e),
                userMessage="读取SSH配置失败",
                cause=e,
            )



    def updateSshConfig(self,updateRequest:SshConfigUpdate)->SshConfig:
        configPath = Path("/etc/ssh/sshd_config")
        if not configPath.exists():
            raise SecurityStatusReadException(
                innerMessage="未找到 sshd 配置文件",
                userMessage="更新SSH配置失败",
            )

        currentConfig = self.getSshConfig()
        self._validateSshConfigUpdate(updateRequest)
        mergedConfig = {
            "Port": updateRequest.port if updateRequest.port is not None else currentConfig.port,
            "PermitRootLogin": updateRequest.permitRootLogin if updateRequest.permitRootLogin is not None else currentConfig.permitRootLogin,
            "PasswordAuthentication": updateRequest.passwordAuthentication if updateRequest.passwordAuthentication is not None else currentConfig.passwordAuthentication,
            "AllowUsers": updateRequest.allowUsers if updateRequest.allowUsers is not None else currentConfig.allowUsers,
            "AllowGroups": updateRequest.allowGroups if updateRequest.allowGroups is not None else currentConfig.allowGroups,
            "ListenAddress": updateRequest.listenAddress if updateRequest.listenAddress is not None else currentConfig.listenAddress,
            "Protocol": updateRequest.protocol if updateRequest.protocol is not None else currentConfig.protocol,
            "LoginGraceTime": updateRequest.loginGraceTime if updateRequest.loginGraceTime is not None else currentConfig.loginGraceTime,
            "MaxAuthTries": updateRequest.maxAuthTries if updateRequest.maxAuthTries is not None else currentConfig.maxAuthTries,
        }

        originalContent = configPath.read_text(encoding="utf-8", errors="ignore")
        contentWithoutManaged = self._removeManagedSshBlock(originalContent)
        managedBlock = self._bulidMangedSshBlock(mergedConfig)
        newContent = contentWithoutManaged.rstrip() + "\n\n" + managedBlock + "\n"

        try:
            try:
                configPath.write_text(newContent, encoding="utf-8")
            except PermissionError:
                writeResult = subprocess.run(
                    ["sudo", "-n", "tee", str(configPath)],
                    input=newContent,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if writeResult.returncode != 0:
                    raise SecurityStatusReadException(
                        innerMessage=writeResult.stderr or writeResult.stdout or "写入sshd配置失败",
                        userMessage="更新SSH配置失败",
                    )

            result = subprocess.run(
                ["sudo", "-n", "sshd", "-t"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                try:
                    configPath.write_text(originalContent, encoding="utf-8")
                except PermissionError:
                    subprocess.run(
                        ["sudo", "-n", "tee", str(configPath)],
                        input=originalContent,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                raise SecurityStatusReadException(
                    innerMessage=result.stderr or result.stdout or "sshd语法检查失败",
                    userMessage="更新SSH配置失败",
                )

            return self.getSshConfig()
        except SecurityStatusReadException:
            raise
        except Exception as e:
            raise SecurityStatusReadException(
                innerMessage=str(e),
                userMessage="更新SSH配置失败",
                cause=e,
            )

    def updateSecuritySwitchState(self, updateRequest: SecuritySwitchUpdate) -> SecuritySwitchState:
        if updateRequest.sshServiceEnabled is not None:
            sshAction = "start" if updateRequest.sshServiceEnabled else "stop"
            try:
                self._callPrivilegedAgent(
                    PrivilegedAction.SERVICE_SET_STATE,
                    {"serviceName": "sshd", "action": sshAction},
                    "更新SSH服务状态失败",
                )
            except Exception as e1:
                try:
                    self._callPrivilegedAgent(
                        PrivilegedAction.SERVICE_SET_STATE,
                        {"serviceName": "ssh", "action": sshAction},
                        "更新SSH服务状态失败",
                    )
                except Exception as e2:
                    raise SecurityStatusReadException(
                        innerMessage=f"sshd更新失败: {e1}; ssh更新失败: {e2}",
                        userMessage="更新SSH服务状态失败",
                        cause=e2,
                    )

        if updateRequest.firewallEnabled is not None:
            try:
                self._callPrivilegedAgent(
                    PrivilegedAction.FIREWALL_SET_ENABLED,
                    {"enabled": updateRequest.firewallEnabled},
                    "更新防火墙状态失败",
                )
            except Exception as e:
                raise SecurityStatusReadException(
                    innerMessage=self._innerMessage(e),
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
            ipVersion=rule.ipVersion,
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
            createdRule = self._callPrivilegedAgent(
                PrivilegedAction.FIREWALL_ADD_PORT_RULE,
                {
                    "port": rule.port,
                    "protocol": self._toToolProtocol(rule.protocol),
                    "ipVersion": rule.ipVersion,
                    "sourceIp": rule.sourceIp,
                    "destinationIp": rule.destinationIp,
                    "priority": rule.priority,
                    "action": rule.action,
                },
                "新增端口规则失败",
            )
        except (BuiltinToolExecutionException, ExecutePermissionDeniedException):
            raise
        except Exception as e:
            raise BuiltinToolExecutionException(
                innerMessage=self._innerMessage(e),
                userMessage="新增端口规则失败",
                cause=e,
            )

        self.__fallbackPortRules.append(fallbackRule)
        self.__nextFallbackPortRuleId += 1
        rules = self.getPortRules()
        for item in reversed(rules):
            if item.port == createdRule["port"] and item.protocol == self._toApiProtocol(createdRule["protocol"]):
                return item

        return rules[-1] if rules else PortRule(
            id=1,
            port=rule.port,
            protocol=rule.protocol,
            ipVersion=rule.ipVersion,
            sourceIp=rule.sourceIp,
            destinationIp=rule.destinationIp,
            priority=rule.priority,
            action=rule.action,
            createdTime=now,
            updatedTime=now,
        )
    
    def getPortRules(self) -> List[PortRule]:
        try:
            toolRules = self._callPrivilegedAgent(
                PrivilegedAction.FIREWALL_LIST_RULES,
                {},
                "读取端口规则失败",
            )
            if not toolRules and self.__fallbackPortRules:
                return list(self.__fallbackPortRules)

            now = datetime.now()
            apiRules: List[PortRule] = []

            for idx, item in enumerate(toolRules):
                port = int(item["port"])
                protocol = str(item["protocol"])
                source_ip = item.get("sourceIp")
                destination_ip = item.get("destinationIp")
                policy = str(item["policy"])
                ip_version = int(item.get("ipVersion") or self._detectIpVersion(source_ip, destination_ip))
                apiRules.append(
                    PortRule(
                        id=self._nextRuleId(idx),
                        port=port,
                        protocol=self._toApiProtocol(protocol),
                        ipVersion=ip_version,
                        sourceIp=source_ip or self._defaultAnyByIpVersion(ip_version),
                        destinationIp=destination_ip or self._defaultAnyByIpVersion(ip_version),
                        priority=100,
                        action=self._toApiAction(policy),
                        createdTime=now,
                        updatedTime=now,
                    )
                )

            return apiRules
        except Exception as e:
            if self.__fallbackPortRules:
                return list(self.__fallbackPortRules)
            raise BuiltinToolExecutionException(
                innerMessage=self._innerMessage(e),
                userMessage="读取端口规则失败",
                cause=e,
            )

    def getSshLogs(self) -> dict:
        try:
            rawLogs = self._callPrivilegedAgent(
                PrivilegedAction.SSH_LIST_LOGS,
                {"maxLines": 500},
                "读取SSH登录日志失败",
            )
            sshLogs = [SshLog.model_validate(item) for item in rawLogs]
            return {
                "total": len(sshLogs),
                "list": [item.model_dump() for item in sshLogs],
            }
        except Exception as e:
            raise BuiltinToolExecutionException(
                innerMessage=self._innerMessage(e),
                userMessage="读取SSH登录日志失败",
                cause=e,
            )

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

    def _defaultAnyByIpVersion(self, ipVersion: int) -> str:
        return "::/0" if ipVersion == 6 else "0.0.0.0/0"

    def _detectIpVersion(self, sourceIp: str | None, destinationIp: str | None) -> int:
        for candidate in [sourceIp, destinationIp]:
            if candidate and ":" in str(candidate):
                return 6
        return 4

    def _parseSshConfigFiles(self, filePaths: List[Path]) -> dict[str, List[str]]:
        parsed: dict[str, List[str]] = {}

        for path in filePaths:
            if not path.exists() or not path.is_file():
                continue

            for rawLine in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = rawLine.strip()
                if not line or line.startswith("#"):
                    continue

                noComment = line.split("#", 1)[0].strip()
                if not noComment:
                    continue

                parts = noComment.split(None, 1)
                if len(parts) < 2:
                    continue

                key = parts[0].strip().lower()
                value = parts[1].strip()
                if not value:
                    continue

                if key in ["allowusers", "allowgroups", "listenaddress", "include"]:
                    items = [item for item in value.split() if item]
                    parsed.setdefault(key, []).extend(items)
                else:
                    parsed.setdefault(key, []).append(value)

        return parsed

    def _safeInt(self, value: str, default: int) -> int:
        try:
            return int(str(value).strip())
        except Exception:
            return default

    def _parseDurationToSeconds(self, value: str, default: int) -> int:
        text = str(value).strip().lower()
        matched = re.match(r"^(\d+)([smhd]?)$", text)
        if not matched:
            return default

        amount = int(matched.group(1))
        unit = matched.group(2)
        if unit == "m":
            return amount * 60
        if unit == "h":
            return amount * 3600
        if unit == "d":
            return amount * 86400
        return amount
    
    def _validateSshConfigUpdate(self,updateRequest:SshConfigUpdate)->None:
        if updateRequest.port is not None and not (1<=updateRequest.port<=65535):
            raise SecurityStatusReadException(
                innerMessage=f"非法端口:{updateRequest.port}",
                userMessage="更新SSH配置失败",
            )
        if updateRequest.protocol is not None and updateRequest.protocol not in [2]:
            raise SecurityStatusReadException(
            innerMessage=f"非法协议版本: {updateRequest.protocol}",
            userMessage="更新SSH配置失败",
        )
        if updateRequest.permitRootLogin is not None and updateRequest.permitRootLogin not in [
            "yes",
            "no",
            "prohibit-password",
            "without-password",
        ]:
            raise SecurityStatusReadException(
                innerMessage=f"非法 PermitRootLogin: {updateRequest.permitRootLogin}",
                userMessage="更新SSH配置失败",
            )

        if updateRequest.passwordAuthentication is not None and updateRequest.passwordAuthentication not in [
            "yes",
            "no",
        ]:
            raise SecurityStatusReadException(
                innerMessage=f"非法 PasswordAuthentication: {updateRequest.passwordAuthentication}",
                userMessage="更新SSH配置失败",
            )

        if updateRequest.loginGraceTime is not None and updateRequest.loginGraceTime <= 0:
            raise SecurityStatusReadException(
                innerMessage=f"非法 LoginGraceTime: {updateRequest.loginGraceTime}",
                userMessage="更新SSH配置失败",
            )

        if updateRequest.maxAuthTries is not None and updateRequest.maxAuthTries <= 0:
            raise SecurityStatusReadException(
                innerMessage=f"非法 MaxAuthTries: {updateRequest.maxAuthTries}",
                userMessage="更新SSH配置失败",
            )
        


    def _bulidMangedSshBlock(self,mergedConfig:dict) -> str:
        allowUsers = mergedConfig["AllowUsers"]
        allowGroups = mergedConfig["AllowGroups"]
        listenAddress = mergedConfig["ListenAddress"]

        lines = [
            "# PANEL_MANAGED_BEGIN",
            f"Port {mergedConfig['Port']}",
            f"PermitRootLogin {mergedConfig['PermitRootLogin']}",
            f"PasswordAuthentication {mergedConfig['PasswordAuthentication']}",
            f"Protocol {mergedConfig['Protocol']}",
            f"LoginGraceTime {mergedConfig['LoginGraceTime']}",
            f"MaxAuthTries {mergedConfig['MaxAuthTries']}",
        ]

        if allowUsers:
            lines.append(f"AllowUsers {' '.join(allowUsers)}")
        if allowGroups:
            lines.append(f"AllowGroups {' '.join(allowGroups)}")
        if listenAddress:
            lines.append(f"ListenAddress {' '.join(listenAddress)}")

        lines.append("# PANEL_MANAGED_END")
        return "\n".join(lines)
    
    def _removeManagedSshBlock(self,content:str) ->str:
        pattern = r"# PANEL_MANAGED_BEGIN.*?# PANEL_MANAGED_END\s*"
        return re.sub(pattern,"",content,flags=re.S)
