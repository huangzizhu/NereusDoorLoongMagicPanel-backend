from gateway.Singleton import Singleton, singletonInit
from gateway.dao.FileDaoInterface import FileDaoInterface
from gateway.orm.OrmEngine import OrmEngine


class FileDaoOrm(FileDaoInterface):

    @singletonInit
    def __init__(self):
        super().__init__('fileDaoOrm')
        self.engine = OrmEngine()
        # 保存 Session 工厂
        self.SessionLocal = self.engine.createSessionFactory()