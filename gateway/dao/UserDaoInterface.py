from abc import abstractmethod
from gateway.Singleton import Singleton
from pojo.User import UserLoginRequest,UserResponse


class UserDaoInterface(Singleton):
    def __init__(self,name: str):
        self.name = name

    @abstractmethod
    def checkUser(self, userLoginRequest: UserLoginRequest)-> UserResponse:
        pass
