from enum import Enum
from abc import ABC, abstractmethod
from typing import Callable, List
from dataclasses import dataclass

from orion.ast import ast

class ObjectType(Enum):
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    STRING = "STRING"
    NULL = "NULL"
    RETURN_VALUE = "RETURN_VALUE"
    FUNCTION = "FUNCTION"
    BUILTIN = "BUILTIN"
    ARRAY = "ARRAY"
    HASH = "HASH"
    MODULE = "MODULE"
    COMPONENT = "COMPONENT"

class Object(ABC):
    @abstractmethod
    def object_type(self) -> ObjectType: pass
    @abstractmethod
    def to_string(self) -> str: pass
    def __str__(self) -> str: return self.to_string()

# --- Hashable Infrastructure ---
class Hashable(ABC):
    @abstractmethod
    def hash_key(self) -> 'HashKey': pass

@dataclass(frozen=True)
class HashKey:
    type: ObjectType
    value: any

# --- Concrete Object Types ---
class Integer(Object, Hashable):
    def __init__(self, value: int): self.value = value
    def object_type(self) -> ObjectType: return ObjectType.INTEGER
    def to_string(self) -> str: return str(self.value)
    def hash_key(self) -> HashKey: return HashKey(type=self.object_type(), value=self.value)

class Boolean(Object, Hashable):
    def __init__(self, value: bool): self.value = value
    def object_type(self) -> ObjectType: return ObjectType.BOOLEAN
    def to_string(self) -> str: return "true" if self.value else "false"
    def hash_key(self) -> HashKey: return HashKey(type=self.object_type(), value=self.value)

class String(Object, Hashable):
    def __init__(self, value: str): self.value = value
    def object_type(self) -> ObjectType: return ObjectType.STRING
    def to_string(self) -> str: return self.value
    def hash_key(self) -> HashKey: return HashKey(type=self.object_type(), value=self.value)

class Null(Object):
    def object_type(self) -> ObjectType: return ObjectType.NULL
    def to_string(self) -> str: return "null"

class ReturnValue(Object):
    def __init__(self, value: Object): self.value = value
    def object_type(self) -> ObjectType: return ObjectType.RETURN_VALUE
    def to_string(self) -> str: return self.value.to_string()

class Function(Object):
    def __init__(self, parameters: list[ast.Identifier], body: ast.BlockStatement, env: 'Environment'):
        self.parameters = parameters
        self.body = body
        self.env = env
    def object_type(self) -> ObjectType: return ObjectType.FUNCTION
    def to_string(self) -> str: return f"function({', '.join(str(p) for p in self.parameters)}) {{ ... }}"

class Builtin(Object):
    def __init__(self, fn: Callable[..., Object]): self.fn = fn
    def object_type(self) -> ObjectType: return ObjectType.BUILTIN
    def to_string(self) -> str: return "builtin function"

class Array(Object):
    def __init__(self, elements: list[Object]): self.elements = elements
    def object_type(self) -> ObjectType: return ObjectType.ARRAY
    def to_string(self) -> str: return f"[{', '.join(e.to_string() for e in self.elements)}]"

@dataclass
class HashPair:
    key: Object
    value: Object

class Hash(Object):
    def __init__(self, pairs: dict[HashKey, HashPair]): self.pairs = pairs
    def object_type(self) -> ObjectType: return ObjectType.HASH
    def to_string(self) -> str: return f"{{{', '.join(f'{p.key.to_string()}:{p.value.to_string()}' for p in self.pairs.values())}}}"

class Module(Object):
    def __init__(self, name: str, env: 'Environment'):
        self.name = name
        self.env = env

    def object_type(self) -> ObjectType:
        return ObjectType.MODULE

    def to_string(self) -> str:
        return f"<module '{self.name}'>"

class Component(Object):
    def __init__(self, name: str, properties: Hash):
        self.name = name
        self.properties = properties

    def object_type(self) -> ObjectType:
        return ObjectType.COMPONENT

    def to_string(self) -> str:
        return f"<component '{self.name}'>"

# Singleton instances for performance and convenience
TRUE = Boolean(True)
FALSE = Boolean(False)
NULL = Null()
