from abc import ABC, abstractmethod
from typing import List, Any, TYPE_CHECKING

import ast_nodes as ast
from environment import Environment
from errors import Return

# This is a common pattern to break circular import cycles.
# The import is only done for static type checking, not at runtime.
if TYPE_CHECKING:
    from interpreter import Interpreter


class OrionCallable(ABC):
    """
    An abstract base class for all objects that can be called like a function.
    """
    @abstractmethod
    def arity(self) -> int:
        """Returns the number of arguments the callable expects."""
        raise NotImplementedError

    @abstractmethod
    def call(self, interpreter: 'Interpreter', arguments: List[Any]) -> Any:
        """Executes the callable's logic."""
        raise NotImplementedError

    def __str__(self) -> str:
        return "<native fn>"


class OrionFunction(OrionCallable):
    """
    Represents a user-defined function in Orion.
    """
    def __init__(self, declaration: ast.Function, closure: Environment):
        self.declaration = declaration
        self.closure = closure # The environment where the function was declared.

    def arity(self) -> int:
        """The number of parameters the function declares."""
        return len(self.declaration.params)

    def call(self, interpreter: 'Interpreter', arguments: List[Any]) -> Any:
        """
        Executes the function. This involves creating a new environment for the
        function's scope, binding arguments to parameters, and then executing
        the function's body.
        """
        # Create a new environment for the function's execution.
        # It encloses the function's closure, not the caller's environment.
        # This is what enables lexical scoping.
        environment = Environment(self.closure)
        for i, param in enumerate(self.declaration.params):
            environment.define(param.lexeme, arguments[i])

        try:
            interpreter._execute_block(self.declaration.body, environment)
        except Return as return_value:
            return return_value.value

        # If no 'return' is encountered, functions implicitly return None.
        return None

    def __str__(self) -> str:
        return f"<fn {self.declaration.name.lexeme}>"


class OrionComponent:
    """
    Represents a component declaration's runtime data, primarily its styles.
    """
    def __init__(self, name: str):
        self.name = name
        self.styles = {}
        self.state_styles = {}

    def __str__(self) -> str:
        return f"<component {self.name}>"
