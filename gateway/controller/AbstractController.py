from abc import abstractmethod
from fastapi import APIRouter
from gateway.Singleton import Singleton

class AbstractController(Singleton):

    def __init__(self, name: str, router: APIRouter):
        self.name: str = name
        self.router: APIRouter = router

    @abstractmethod
    def routerSetup(self):
        pass

