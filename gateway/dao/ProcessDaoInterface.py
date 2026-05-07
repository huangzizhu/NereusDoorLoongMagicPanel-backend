from abc import abstractmethod
from gateway.Singleton import Singleton
from gateway.orm.ProcessOrm import ProcessOperationLogOrm
from pojo.Process import ProcessOperationLog
from typing import List

class ProcessDaoInterface(Singleton):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def addLog(self, data: ProcessOperationLogOrm):
        pass

    @abstractmethod
    def getTotal(self) -> int:
        pass

    @abstractmethod
    def getLog(self, page, pageSize) -> List[ProcessOperationLog]:
        pass


