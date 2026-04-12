from gateway.Singleton import singletonInit
from gateway.dao.UserDaoInterface import UserDaoInterface
from gateway.orm.OrmEngine import OrmEngine
from pojo.User import UserLoginRequest, UserResponse
from gateway.orm.UserOrm import UserOrm


class UserDaoOrm(UserDaoInterface):

    @singletonInit
    def __init__(self):
        super().__init__('logDaoOrm')
        self.engine = OrmEngine()
        # 保存 Session 工厂
        self.SessionLocal = self.engine.createSessionFactory()

    def checkUser(self, userLoginRequest: UserLoginRequest)-> UserResponse:
        session = self.SessionLocal()
        pass


