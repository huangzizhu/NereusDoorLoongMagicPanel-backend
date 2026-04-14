from abc import abstractmethod
from typing import Optional

from gateway.Singleton import Singleton
from gateway.orm.UserOrm import UserOrm


class UserDaoInterface(Singleton):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def getUserByAccount(self, account: str) -> Optional[UserOrm]:
        pass
