from Exception.GatewayAbstractException import GatewayAbstractException
class PasswordIncorrectException(GatewayAbstractException):
    def __init__(self, innerMessage: str = None, userMessage: str = "Password is incorrect.", cause: Exception = None):
        super().__init__(innerMessage,userMessage,cause)
