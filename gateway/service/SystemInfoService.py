from typing import List

from Exception.InvalidParamException import InvalidParamException
from Singleton import Singleton, singletonInit
from dao.SystemInfoDaoInterface import SystemInfoDaoInterface
from dao.SystemInfoDao import SystemInfoDao
import time
from ndlmpanel_agent.tools.ops.monitor.system_monitor_tools import (getCpuInfo
,getMemoryInfo,getGpuInfo,getDiskInfo,getNetworkInfo)
from ndlmpanel_agent.models.ops.monitor.system_monitor_models import (CpuInfo
,MemoryInfo,DiskPartitionInfo,GpuInfo,NetworkInterfaceInfo)
from ndlmpanel_agent.tools.ops.misc.system_info_tools import getSystemVersion

from pojo.Common import ListResponse
from pojo.PanelInfo import SystemHealthResponse, AlertQuery,AlertEvent
from Exception.BuiltinToolExecutionException import BuiltinToolExecutionException
from Exception.DataBaseException import DataBaseException

class SystemInfoService(Singleton):
    @singletonInit
    def __init__(self):
        self.systemInfoDao: SystemInfoDaoInterface = SystemInfoDao()

    def _getDiskAverage(self, diskInfos: List[DiskPartitionInfo]) -> float:
        usedSum = 0.0
        allSum = 0.0
        for diskInfo in diskInfos:
            usedSum += diskInfo.usedBytes
            allSum += diskInfo.totalBytes
        if allSum == 0:
            return 0.0  # 避免除以0
        usage = (usedSum / allSum) * 100
        return round(usage, 2)  # 保留2位小数

    def _getHealthCore(self, systemInfo: SystemHealthResponse) -> SystemHealthResponse:
        """
        根据系统资源使用情况计算健康度（满分100）
        算法思路：
        - CPU、内存、磁盘、网卡使用率越高，健康度越低
        - 如果 GPU 信息为空，则动态调整权重
        - 确保遍历每个磁盘分区和网卡接口，获取合理数据
        """
        # 权重分配（根据业务需求动态调整）
        weights = {
            "cpu": 0.3,
            "memory": 0.3,
            "disk": 0.2,
            "network": 0.2,
            "gpu": 0.0,  # 默认 GPU 权重为0，若有 GPU 数据再调整权重
        }

        # CPU 和内存评分（使用率越高越差）
        cpuScore = max(0, 100 - systemInfo.cpuUsage)
        memoryScore = max(0, 100 - systemInfo.memoryUsage)

        # 动态调整磁盘评分和权重
        totalDiskUsage = 0
        if systemInfo.diskInfos:
            for disk in systemInfo.diskInfos:
                totalDiskUsage += disk.usagePercent  # 磁盘使用率
            diskScore = max(0, 100 - (totalDiskUsage / len(systemInfo.diskInfos)))
        else:
            diskScore = 100  # 如果没有磁盘信息，默认健康度为满分

        # 动态调整网络评分
        totalNetworkUsage = 0
        if systemInfo.networkInfos:
            for network in systemInfo.networkInfos:
                totalNetworkUsage += network.recvBytesPerSec + network.sentBytesPerSec
            networkScore = max(0, 100 - (totalNetworkUsage / len(systemInfo.networkInfos)))
        else:
            networkScore = 100  # 如果没有网络信息，默认健康度为满分

        # GPU 评分（如果有 GPU 数据的话）
        gpuScore = 100
        if systemInfo.gpuInfos:
            weights["gpu"] = 0.2  # 如果有 GPU，给 GPU 评分一个权重
            totalGpuUsage = 0
            for gpu in systemInfo.gpuInfos:
                totalGpuUsage += gpu.utilizationPercent
            gpuScore = max(0, 100 - (totalGpuUsage / len(systemInfo.gpuInfos)))

        # 计算健康分数
        healthScore = (
                cpuScore * weights["cpu"] +
                memoryScore * weights["memory"] +
                diskScore * weights["disk"] +
                networkScore * weights["network"] +
                gpuScore * weights["gpu"]
        )

        # 四舍五入为整数
        healthScore = int(round(healthScore))

        # 根据健康分数分类 status
        if healthScore >= 80:
            status = 0  # 正常
        elif healthScore >= 50:
            status = 1  # 警告
        else:
            status = 2  # 异常

        # 更新返回的系统健康信息
        systemInfo.healthScore = healthScore
        systemInfo.status = status

        return systemInfo



    def getSystemInfo(self) -> SystemHealthResponse:
        try:
            cpuInfo: CpuInfo = getCpuInfo()
            memoryInfo: MemoryInfo = getMemoryInfo()
            diskInfos: List[DiskPartitionInfo] = getDiskInfo()
            networkInfos: List[NetworkInterfaceInfo] = getNetworkInfo()
            gpuInfos: List[GpuInfo] = getGpuInfo()
            hostname = getSystemVersion().hostName
        except Exception as e:
            raise BuiltinToolExecutionException(innerMessage=str(e),userMessage="查询系统状态出错，请重试或联系管理员",cause=e)
        res = SystemHealthResponse(
            hostname=hostname,
            cpuUsage=cpuInfo.usagePercent,
            memoryUsage=memoryInfo.usagePercent,
            diskUsage=self._getDiskAverage(diskInfos),
            healthScore=0,#先随便点
            status=1,
            cpuInfo=cpuInfo,
            memoryInfo=memoryInfo,
            gpuInfos=gpuInfos,
            diskInfos=diskInfos,
            networkInfos=networkInfos,
        )
        return self._getHealthCore(res)

    def getAllSystemAlerts(self, alertQuery: AlertQuery) -> ListResponse:
        try:
            total: int = self.systemInfoDao.getAllSystemAlertsCount(alertQuery.excludeProcessed)
            items: List[AlertEvent] = self.systemInfoDao.getAllSystemAlerts(alertQuery)
            return ListResponse(total=total, items=items)
        except Exception as e:
            raise DataBaseException(innerMessage=str(e),userMessage="数据库操作错误，请重试或联系管理员",cause=e)

    def setAlertsRead(self, id: int) -> AlertEvent:
        try:
            countRow: int = self.systemInfoDao.setAlertsRead(id)
            if not countRow:
                raise InvalidParamException(userMessage=f"id为{id}的警告事件不存在！")
            return self.systemInfoDao.getAlertEventById(id)
        except InvalidParamException:
            raise
        except Exception as e:
            raise DataBaseException(innerMessage=str(e),userMessage="数据库操作错误，请重试或联系管理员",cause=e)

    def setAlertsProcess(self, id: int) -> AlertEvent:
        try:
            countRow: int = self.systemInfoDao.setAlertsProcess(id)
            if not countRow:
                raise InvalidParamException(userMessage=f"id为{id}的警告事件不存在！")
            return self.systemInfoDao.getAlertEventById(id)
        except InvalidParamException:
            raise
        except Exception as e:
            raise DataBaseException(innerMessage=str(e), userMessage="数据库操作错误，请重试或联系管理员", cause=e)





