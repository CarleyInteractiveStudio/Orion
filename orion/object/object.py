from enum import Enum
from abc import ABC, abstractmethod

from orion.ast import ast

class ObjectType(Enum):
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"
    NULL = "NULL"
    RETURN_VALUE = "RETURN_VALUE"
    FUNCTION = "FUNCTION"

class Object(ABC):
    @abstractmethod
    def object_type(self) -> ObjectType:
        pass

    @abstractmethod
    def to_string(self) -> str:
        pass

    def __str__(self) -> str:
        return self.to_string()

class Integer(Object):
    def __init__(self, value: int):
        self.value = value

    def object_type(self) -> ObjectType:
        return ObjectType.INTEGER

    def to_string(self) -> str:
        return str(self.value)

class Boolean(Object):
    def __init__(self, value: bool):
        self.value = value

    def object_type(self) -> ObjectType:
        return ObjectType.BOOLEAN

    def to_string(self) -> str:
        return "true" if self.value else "false"

class String(Object):
    def __init__(self, value: str):
        self.value = value

    def object_type(self) -> ObjectType:
        return ObjectType.STRING

    def to_string(self) -> str:
        return self.value

class Null(Object):
    def object_type(self) -> ObjectType:
        return ObjectType.NULL

    def to_string(self) -> str:
        return "null"

class ReturnValue(Object):
    def __init__(self, value: Object):
        self.value = value

    def object_type(self) -> ObjectType:
        return ObjectType.RETURN_VALUE

    def to_string(self) -> str:
        return self.value.to_string()

class Function(Object):
    def __init__(self, parameters: list[ast.Identifier], body: ast.BlockStatement, env: 'Environment'):
        self.parameters = parameters
        self.body = body
        self.env = env

    def object_type(self) -> ObjectType:
        return ObjectType.FUNCTION

    def to_string(self) -> str:
        params = ", ".join(str(p) for p in self.parameters)
        return f"function({params}) {{\n  {self.body}\n}}"

# Singleton instances for performance and convenience
TRUE = Boolean(True)
FALSE = Boolean(False)
NULL = Null()
