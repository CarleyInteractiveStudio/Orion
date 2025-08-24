from tokens import Token

class OrionRuntimeError(RuntimeError):
    """Custom exception for reporting runtime errors."""
    def __init__(self, token: Token, message: str):
        self.token = token
        self.message = message
        super().__init__(self.message)
