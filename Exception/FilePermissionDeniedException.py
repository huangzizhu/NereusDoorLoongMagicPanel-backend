from Exception.GatewayAbstractException import GatewayAbstractException


class FilePermissionDeniedException(GatewayAbstractException):
    def __init__(self, innerMessage: str = None, userMessage: str = None, cause: Exception = None):
        super().__init__(innerMessage,userMessage,cause)