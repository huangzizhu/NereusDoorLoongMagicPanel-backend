from dao.FileDaoInterface import FileDaoInterface
from dao.FileDaoOrm import FileDaoOrm
from gateway.Singleton import Singleton,singletonInit

class FileService(Singleton):
    @singletonInit
    def __init__(self):
        self.fileDao: FileDaoInterface = FileDaoOrm()

