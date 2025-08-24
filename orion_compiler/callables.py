from abc import ABC, abstractmethod
from typing import List, Any, TYPE_CHECKING

import ast_nodes as ast
from environment import Environment
from errors import Return
from errors import OrionRuntimeError

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
            environment.define(param.name.lexeme, arguments[i])

        try:
            interpreter._execute_block(self.declaration.body, environment)
        except Return as return_value:
            return return_value.value

        # If no 'return' is encountered, functions implicitly return None.
        return None

    def bind(self, instance: 'OrionInstance') -> 'OrionFunction':
        """Binds 'this' to a specific instance."""
        environment = Environment(self.closure)
        environment.define("this", instance)
        return OrionFunction(self.declaration, environment)

    def __str__(self) -> str:
        return f"<fn {self.declaration.name.lexeme}>"


class OrionInstance:
    """Base class for anything that has fields."""
    def __init__(self):
        self.fields = {}

    def get(self, name: 'Token'):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]
        raise OrionRuntimeError(name, f"Undefined property '{name.lexeme}'.")

    def set(self, name: 'Token', value: Any):
        self.fields[name.lexeme] = value

    def __str__(self):
        return "<instance>"


class OrionComponent(OrionInstance, OrionCallable):
    """
    Represents a component declaration. It's callable and produces instances.
    """
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.fields["styles"] = {}
        self.fields["state_styles"] = {}

    def arity(self) -> int:
        # For now, component constructors don't take arguments.
        return 0

    def call(self, interpreter: 'Interpreter', arguments: List[Any]) -> Any:
        instance = OrionInstance()
        # The new instance inherits the base styles of the component.
        instance.fields = self.fields["styles"].copy()
        return instance

    def __str__(self) -> str:
        return f"<component {self.name}>"
