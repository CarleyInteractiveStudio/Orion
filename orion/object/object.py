from enum import Enum
from abc import ABC, abstractmethod

class ObjectType(Enum):
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"
    NULL = "NULL"
    RETURN_VALUE = "RETURN_VALUE"

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

# Singleton instances for performance and convenience
TRUE = Boolean(True)
FALSE = Boolean(False)
NULL = Null()
