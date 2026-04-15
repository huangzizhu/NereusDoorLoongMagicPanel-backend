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

    @abstractmethod
    def insertTokens(self, tokenOrm: UserOrm):
        pass

    @abstractmethod
    def deleteTokensByRefreshToken(self, refreshToken: str) -> int:
        pass

    @abstractmethod
    def deactivateTokensByRefreshToken(self, refreshToken: str) -> int:
        pass

    @abstractmethod
    def getUserByRefreshToken(self, refreshToken) -> UserOrm | None:
        pass
