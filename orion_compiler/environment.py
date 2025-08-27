from typing import Dict, Any, Optional

from . tokens import Token
from . errors import OrionRuntimeError

class Environment:
    """
    Manages variable scopes, storing and retrieving variable values.
    """
    def __init__(self, enclosing: Optional['Environment'] = None):
        self.values: Dict[str, Any] = {}
        self.enclosing: Optional['Environment'] = enclosing

    def define(self, name: str, value: Any):
        """
        Defines a new variable in the current scope.
        This is used for 'var' declarations.
        """
        self.values[name] = value

    def get(self, name: Token) -> Any:
        """
        Retrieves the value of a variable.
        If not found in the current scope, it checks the enclosing scope.
        """
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name)

        raise OrionRuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def assign(self, name: Token, value: Any):
        """
        Assigns a new value to an existing variable.
        If not found in the current scope, it checks the enclosing scope.
        """
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise OrionRuntimeError(name, f"Undefined variable '{name.lexeme}'.")
