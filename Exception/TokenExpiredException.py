from Exception.GatewayAbstractException import GatewayAbstractException
import warnings
class TokenExpiryException(GatewayAbstractException):


    #已废弃
    def __init__(self, innerMessage: str = None, userMessage: str = "Password is incorrect.", cause: Exception = None):
        warnings.warn(
            f"{self.__class__.__name__} 已废弃，请使用 NewClass",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(innerMessage,userMessage,cause)