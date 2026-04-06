from abc import abstractmethod
from gateway.Singleton import Singleton
class UserDaoInterface(Singleton):
    def __init__(self,name: str):
        self.name = name
