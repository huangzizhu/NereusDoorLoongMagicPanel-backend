
class GatewayAbstractException(Exception):

    def __init__(self, innerMessage: str = None, userMessage: str = None, cause: Exception = None):
        self.innerMessage = innerMessage
        self.userMessage = userMessage
        self.cause = cause
