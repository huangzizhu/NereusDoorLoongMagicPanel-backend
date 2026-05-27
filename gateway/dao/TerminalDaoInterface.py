from abc import abstractmethod
from typing import List

from gateway.Singleton import Singleton
from pojo.Terminal import TerminalSessionAdminAuthUpdate, TerminalSessionCloseUpdate, TerminalSessionLog, \
    TerminalSessionLogCreate


class TerminalDaoInterface(Singleton):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def insertSession(self, sessionLog: TerminalSessionLogCreate):
        pass

    @abstractmethod
    def markAdminAuthResult(self, updateRequest: TerminalSessionAdminAuthUpdate) -> int:
        pass

    @abstractmethod
    def closeSession(self, updateRequest: TerminalSessionCloseUpdate) -> int:
        pass

    @abstractmethod
    def getTotal(self) -> int:
        pass

    @abstractmethod
    def getLog(self, page: int, pageSize: int) -> List[TerminalSessionLog]:
        pass
