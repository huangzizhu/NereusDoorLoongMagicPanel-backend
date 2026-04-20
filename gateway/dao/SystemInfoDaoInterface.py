from abc import abstractmethod
from gateway.Singleton import Singleton
from pojo.PanelInfo import AlertQuery, AlertEvent
from typing import List

class SystemInfoDaoInterface(Singleton):
    def __init__(self,name: str):
        self.name = name

    @abstractmethod
    def getAllSystemAlertsCount(self, excludeProcessed: bool) -> int:
        pass

    @abstractmethod
    def getAllSystemAlerts(self, alertQuery: AlertQuery) -> List[AlertEvent]:
        pass

    @abstractmethod
    def setAlertsRead(self, id: int) -> int:
        pass

    @abstractmethod
    def getAlertEventById(self, id: int) -> AlertEvent:
        pass

    @abstractmethod
    def setAlertsProcess(self, id: int) -> int:
        pass