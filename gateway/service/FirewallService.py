from gateway.Singleton import Singleton, singletonInit
from pojo.FireWall import SecuritySwitchState, SecuritySwitchUpdate
from datetime import datetime
from typing import List
import re
import subprocess
from pojo.FireWall import PortRuleCreate,PortRule, SshConfig,SshConfigUpdate,SshLogBase
from pathlib import Path
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


#测试
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

    def getSshLogBase(self,)->List[SshLogBase]:
        #获取日志
        mainSshLogBasePath=Path("/var/log/auth.log")
        if not mainSshLogBasePath.exists():
            mainSshLogBasePath = Path("/var/log/secure")
        
        try:
            if not mainSshLogBasePath.exists():
                raise FileExistsError(f"SSH日志文件不存在:{mainSshLogBasePath}")
            lines:List[str] = []
            try:
                with open(mainSshLogBasePath,"r",encoding="utf-8",errors="ignore")as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
            except PermissionError:
                res= subprocess.run(["sudo","-n","tail","-n","500",str(mainSshLogBasePath)],capture_output=True,text=True,check=False,)
                if res.returncode !=0:
                    raise PermissionError(res.stderr or "读取日志权限不够")
                lines = [line.strip() for line in res.stdout.splitlines if line.strip()]

            successPattern = re.compile(
                r"^(?P<mon>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2}).*sshd\[\d+\]:\s+Accepted\s+\w+\s+for\s+(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
                re.IGNORECASE,
            )
            failPattern = re.compile(
                r"^(?P<mon>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2}).*sshd\[\d+\]:\s+Failed\s+\w+\s+for\s+(invalid user\s+)?(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+(?P<port>\d+)",
                re.IGNORECASE,
            )

            res:List[SshLogBase] = []
            currentYear = datetime.now().year
            for line in lines:
                if "sshd" not  in line.lower():
                    continue
                m = successPattern.match(line)
                status = "SUCCESS"
                reason = None

                if not m:
                    m = failPattern.match(line)
                    status = "FAILURE"
                    reason = "登录失败"

                if not m:
                    continue

                ts = datetime.strptime(f"{currentYear} {m.group('mon')} {m.group('day')} {m.group('time')}","%Y %b %d %H:%M:%S")
                res.append(
                    SshLogBase(
                        timestamp=ts,
                        user=m.group("user"),
                        sourceIp=m.group("ip"),
                        port=int(m.group("port")),
                        status=status,
                        reason=reason,
                    )
                )
            return res
        
        except PermissionError as e:
            raise SecurityStatusReadException(innerMessage=str(e),userMessage="无法读取SSH日志",cause=e)
        except Exception as e:
            raise SecurityStatusReadException(innerMessage=str(e),userMessage="读取SSH日志失败",cause=e)

        #筛选出ssh相关的日志

        #写入新的日志在返回
        
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
    
