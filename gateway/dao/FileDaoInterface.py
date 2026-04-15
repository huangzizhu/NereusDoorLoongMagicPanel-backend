from abc import abstractmethod
from gateway.Singleton import Singleton


class FileDaoInterface(Singleton):
    def __init__(self,name: str):
        self.name = name