from dataclasses import dataclass

# --- Type System Classes ---

@dataclass(frozen=True)
class Type:
    """Base class for all types in the Orion type system."""
    def __str__(self) -> str:
        return self.name

@dataclass(frozen=True)
class PrimitiveType(Type):
    name: str

@dataclass(frozen=True)
class ListType(Type):
    element_type: Type
    name: str = "list"

    def __str__(self) -> str:
        return f"list[{self.element_type}]"

@dataclass(frozen=True)
class DictType(Type):
    key_type: Type
    value_type: Type
    name: str = "dict"

    def __str__(self) -> str:
        return f"dict[{self.key_type}, {self.value_type}]"

@dataclass(frozen=True)
class ComponentType(Type):
    name: str

    def __str__(self) -> str:
        return self.name

# --- Singleton Instances of Primitive Types ---

ANY = PrimitiveType("any")
NIL = PrimitiveType("nil")
BOOL = PrimitiveType("bool")
NUMBER = PrimitiveType("number")
STRING = PrimitiveType("string")
FUNCTION = PrimitiveType("function")
TYPE = PrimitiveType("type")
COMPONENT = PrimitiveType("component")
MODULE = PrimitiveType("module")

# Convenience instances for common generic types
ANY_LIST = ListType(ANY)
ANY_DICT = DictType(ANY, ANY)
