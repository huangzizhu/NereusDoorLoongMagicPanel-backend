from abc import abstractmethod
from typing import List
from pojo.Log import Log
from gateway.Singleton import Singleton


class LogDaoInterface(Singleton):
    def __init__(self,name: str):
        self.name = name

    @abstractmethod
    def insertLog(self, log: Log):
        pass

    @abstractmethod
    def getAllLogs(self) -> List[Log]:
        pass