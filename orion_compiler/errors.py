from typing import Any
from tokens import Token

class OrionRuntimeError(RuntimeError):
    """Custom exception for reporting runtime errors."""
    def __init__(self, token: Token, message: str):
        self.token = token
        self.message = message
        super().__init__(self.message)

class Return(Exception):
    """
    An exception used for control flow to handle 'return' statements.
    It's not an error, so it inherits from the base Exception.
    """
    def __init__(self, value: Any):
        self.value = value
