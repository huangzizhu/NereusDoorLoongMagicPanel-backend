from gateway.Singleton import Singleton, singletonInit
from pojo.FireWall import SecuritySwitchState, SecuritySwitchUpdate

from ndlmpanel_agent import getFirewallStatus, manageSystemService, ServiceAction
from ndlmpanel_agent.exceptions.tool_exceptions import ToolExecutionException, PermissionDeniedException
from Exception.SecurityStatusReadException import SecurityStatusReadException


class FirewallService(Singleton):
    @singletonInit
    def __init__(self):
        # self.fireWallDao: FireWallDaoInterface = FireWallDaoOrm()
        pass

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