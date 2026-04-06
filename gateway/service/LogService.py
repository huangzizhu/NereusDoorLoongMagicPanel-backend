from typing import List
from gateway.dao.LogDaoInterface import LogDaoInterface
from gateway.dao.LogDaoOrm import LogDaoOrm
from pojo.Log import Log
from Exception.DataBaseException import DataBaseException
from gateway.Singleton import Singleton,singletonInit


class LogService(Singleton):

    @singletonInit
    def __init__(self):
        self.logDao: LogDaoInterface = LogDaoOrm()


    def insertLog(self,log: Log):
        try:
            self.logDao.insertLog(log)
        except Exception:
            pass

    def getAllLogs(self) -> List[Log]:
        try:
            return self.logDao.getAllLogs()
        except Exception as e:
            raise DataBaseException(str(e))


