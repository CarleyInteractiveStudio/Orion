import sys
from typing import Any
from . tokens import Token

def type_error(token: Token, message: str):
    """Reports a type error to stderr."""
    if token.token_type is None and token.lexeme == '<script>': # Special case for top-level script node
        print(f"Type Error: {message}", file=sys.stderr)
    else:
        print(f"[line {token.line}] Type Error at '{token.lexeme}': {message}", file=sys.stderr)

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
