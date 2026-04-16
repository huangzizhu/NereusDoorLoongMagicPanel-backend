from gateway.Singleton import Singleton, singletonInit
from pojo.FireWall import SecuritySwitchState

from ndlmpanel_agent import getFirewallStatus, manageSystemService, ServiceAction
from ndlmpanel_agent.exceptions.tool_exceptions import ToolExecutionException, PermissionDeniedException
from Exception.SecurityStatusReadException import SecurityStatusReadException
class FirewallService(Singleton):
    @singletonInit
    def __init__(self):
        #self.fireWallDao: FireWallDaoInterface = FireWallDaoOrm()
        pass

    def readWindowsFirewallEnabled(self) -> bool:
        #读取windows防火墙是否启用
        try:
            firewallStatus = getFirewallStatus()
            return bool(firewallStatus.isActive)
        except (ToolExecutionException, PermissionDeniedException)as e:
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

    def readSshServiceEnabled(self)->bool:
        try:
            result = manageSystemService("sshd",action=ServiceAction.STATUS)
        except Exception as e:
            firstError=e
            try:
                result=manageSystemService("ssh",action=ServiceAction.STATUS)
            except Exception as e2:
                raise SecurityStatusReadException(
                    innerMessage=f"sshd状态读取失败:{firstError};ssh状态读取失败:{e2}",
                    userMessage="读取ssh服务状态失败",
                    cause=e2,
                )

        statusText=(result.currentStatus or "").strip().lower()
        return statusText in ["running","active","enabled"]
        
        
    def getSecuritySwitchState(self) -> SecuritySwitchState:
        return SecuritySwitchState(
            firewallEnabled=self.readWindowsFirewallEnabled(),
            sshServiceEnabled=self.readSshServiceEnabled(),
        )