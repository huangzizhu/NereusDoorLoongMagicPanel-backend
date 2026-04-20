from Exception.GatewayAbstractException import GatewayAbstractException

class SecurityStatusReadException(GatewayAbstractException):
    def __init__(self, innerMessage: str = None, userMessage: str = "读取安全开关状态失败", cause: Exception = None):
        super().__init__(innerMessage, userMessage, cause)