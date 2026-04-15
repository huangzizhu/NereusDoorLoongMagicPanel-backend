from fastapi import APIRouter

from gateway.Response import ResponseModel, Response
from gateway.Singleton import singletonInit
from gateway.controller.AbstractController import AbstractController
from service.FileService import FileService


class FileController(AbstractController):
    @singletonInit
    def __init__(self):
        self.router = APIRouter(prefix="/file", tags=["文件管理"])
        self.fileService: FileService = FileService()
        super().__init__("fileController", self.router)
        self.routerSetup()

    def routerSetup(self):
        pass
