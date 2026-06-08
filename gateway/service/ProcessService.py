import random
import signal
from time import sleep

from utils.toolFunction import getZombieOrphanProcesses, ProcessInfo, batchKillProcesses
from sqlalchemy import true

from Exception.BuiltinToolExecutionException import BuiltinToolExecutionException
from Exception.DataBaseException import DataBaseException
from Exception.ExecutePermissionDeniedException import ExecutePermissionDeniedException
from Exception.InvalidParamException import InvalidParamException
from gateway.dao.ProcessDaoOrm import ProcessDaoOrm
from gateway.dao.ProcessDaoInterface import ProcessDaoInterface
from gateway.Singleton import singletonInit,Singleton
from utils.toolFunction.models.ops.process.process_models import ProcessInfo, ProcessSortBy, ProcessKillResult, \
    ProcessDetailInfo, ProcessAutoCleanResult, BatchKillResult, BatchKillMode
from utils.toolFunction.tools.ops.process.process_tools import listProcesses,killProcess,getProcessDetail,autoCleanProcesses
from utils.toolFunction.exceptions.tool_exceptions import ResourceNotFoundException, PermissionDeniedException, \
    ToolExecutionException
from gateway.orm.ProcessOrm import ProcessOperationLogOrm
from typing import List

from pojo.Common import PageSearchRequest, ListResponse
from pojo.Process import KillProcessRequest, AutoCleanRequest, BatchKillProcessRequest, ProcessOperationLog
import queue
import threading


class ProcessOrmItem:
    def __init__(self,data: ProcessOperationLogOrm):
        self.retry: int = 0
        self.data: ProcessOperationLogOrm = data

class ProcessService(Singleton):
    @singletonInit
    def __init__(self):
        self.processDao: ProcessDaoInterface = ProcessDaoOrm()
        self.logQueue = queue.Queue(maxsize=100)
        self.isConsumerStart = False
        self._startLogConsumer()

    def logConsumer(self):
        while True:
            logItem: ProcessOrmItem = self.logQueue.get()
            try:
                self.processDao.addLog(logItem.data)
            except queue.Empty:
                # 队列空，继续循环
                continue
            except Exception as e:
                if logItem is not None:
                    logItem.retry += 1
                    if logItem.retry <= 5:
                        try:
                            # 非阻塞入队，避免队列满卡死
                            self.logQueue.put(logItem, block=False)
                        except queue.Full:
                            # 队列满了，只能丢弃，防止爆内存
                            pass
                    sleep(random.uniform(1, 5))#随机退避
            finally:
                if logItem is not None:
                    self.logQueue.task_done()



    def _startLogConsumer(self,):
        if not self.isConsumerStart:
            t = threading.Thread(target=self.logConsumer,daemon=True)
            t.start()
            self.isConsumerStart = True\

    def addLog(self,data: ProcessOperationLogOrm):
        try:
            self.logQueue.put(ProcessOrmItem(data))
        except Exception as e:
            pass

    def getProcessInfo(self, sortedBy: int, keyword: str):
        sortedByStr = ProcessSortBy.CPU
        if sortedBy == 0:
            sortedByStr = ProcessSortBy.CPU
        elif sortedBy == 1:
            sortedByStr = ProcessSortBy.MEMORY
        elif sortedBy == 2:
            sortedByStr = ProcessSortBy.PID
        else:
            raise InvalidParamException(userMessage=f"sortedBy不合法,应当为0，1，2，实际为{sortedBy}")
        try:
            return listProcesses(sortedByStr, keyword)
        except Exception as e:
            raise BuiltinToolExecutionException(userMessage=f"获取进程列表失败")

    def _killProcess(self,killRequest: KillProcessRequest,signal,operationType):
        try:
            res: ProcessKillResult = killProcess(killRequest.pid,signal)
            logOrm = ProcessOperationLogOrm(operationType=operationType,
                                           targetPids=str(killRequest.pid),
                                           operator="user",
                                           reason=killRequest.reason[:500],
                                           result=("success" if res.success else res.errorMessage)[:20])
            self.addLog(logOrm)
            return res
        except ResourceNotFoundException as e:
            raise InvalidParamException(userMessage=e.innerMessage)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(userMessage=e.innerMessage)

    def killProcess(self, killRequest: KillProcessRequest) -> ProcessKillResult:
         return self._killProcess(killRequest, 15, "normal-kill")

    def forceKillProcess(self, killRequest: KillProcessRequest) -> ProcessKillResult:
        return self._killProcess(killRequest, 9, "Force-Kill")

    def getProcessDetail(self, pid: int) -> ProcessDetailInfo:
        if pid <= 0:
            raise InvalidParamException(userMessage=f"pid 不能为{pid}")
        try:
            res: ProcessDetailInfo = getProcessDetail(pid)
            return res
        except ResourceNotFoundException as e:
            raise InvalidParamException(userMessage=e.innerMessage)
        except PermissionDeniedException as e:
            raise ExecutePermissionDeniedException(userMessage=e.innerMessage)

    def autoClean(self, request: AutoCleanRequest) -> ProcessAutoCleanResult:
        try:
            res: ProcessAutoCleanResult = autoCleanProcesses(request.cpuThreshold,request.memoryThreshold)
            pids = []
            for pid in res.killedProcesses:
                pids.append(str(pid))
            targetPids = ",".join(pids)
            result = "totalKilled:" + str(res.totalKilled) + "\n" + "totalScanned:" +str(res.totalScanned)
            logOrm = ProcessOperationLogOrm(operationType="autoclean",
                                            targetPids=targetPids[:1000],
                                            operator="user",
                                            reason="autoclean",
                                            result=result[:20])
            self.addLog(logOrm)
            return res
        except ToolExecutionException as e:
            raise BuiltinToolExecutionException(userMessage=e.innerMessage)

    def getZombies(self) -> list[ProcessInfo] | None:
        try:
            res: List[ProcessInfo] = getZombieOrphanProcesses()
            return res
        except Exception as e:
            raise BuiltinToolExecutionException(cause=e,innerMessage=str(e),userMessage="执行错误")

    def _batchKillProcess(self,request: BatchKillProcessRequest, operationType: str, signal: BatchKillMode) -> BatchKillResult:
        try:
            res: BatchKillResult = batchKillProcesses(request.pids,signal)
            pids = []
            detailList = ["totalRequested:",str(res.totalRequested),"\n","totalSuccess:",str(res.totalSuccess),"\n","totalFailed:",str(res.totalFailed),"\n"]
            for killRes in res.results:
                pids.append(str(killRes.pid))
                detailList.append(str(killRes.pid))
                detailList.append(":")
                detailList.append(str("success" if killRes.success else killRes.errorMessage))
                detailList.append("\n")
            targetPids = ",".join(pids)
            detail = "".join(detailList)
            logOrm = ProcessOperationLogOrm(operationType=operationType,
                                            targetPids=targetPids[:1000],
                                            operator="user",
                                            reason=request.reason,
                                            result="success",
                                            detail=detail[:1000])
            self.addLog(logOrm)
            return res

        except Exception as e:
            raise BuiltinToolExecutionException(cause=e, innerMessage=str(e), userMessage="执行错误")

    def batchKillProcess(self, request: BatchKillProcessRequest) -> BatchKillResult:
        return self._batchKillProcess(request, "batchKillProcess", BatchKillMode.SIGTERM)


    def batchForceKillProcess(self,request: BatchKillProcessRequest) -> BatchKillResult:
        return self._batchKillProcess(request, "batchForceKillProcess", BatchKillMode.SIGKILL)

    def getLog(self, request: PageSearchRequest) -> ListResponse:
        try:
            total: int = self.processDao.getTotal()
            items: List[ProcessOperationLog] = self.processDao.getLog(request.page,request.pageSize)
            return ListResponse(total=total,items=items)
        except Exception as e:
            raise DataBaseException(innerMessage=str(e),userMessage="数据库异常",cause=e)

















