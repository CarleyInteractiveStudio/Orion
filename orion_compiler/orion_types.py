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

@dataclass(frozen=True)
class ClassType(Type):
    name: str

    def __str__(self) -> str:
        return self.name

@dataclass(frozen=True)
class FunctionType(Type):
    param_types: list['Type']
    return_type: 'Type'
    is_variadic: bool = False
    name: str = "function"

    def __str__(self) -> str:
        if self.is_variadic:
            param_str = "..."
        else:
            param_str = ", ".join(map(str, self.param_types))
        return f"function({param_str}) -> {self.return_type}"

# --- Singleton Instances of Primitive Types ---

ANY = PrimitiveType("any")
NIL = PrimitiveType("nil")
BOOL = PrimitiveType("bool")
NUMBER = PrimitiveType("number")
STRING = PrimitiveType("string")
FUNCTION = FunctionType([], ANY) # Generic function type
TYPE = PrimitiveType("type")
CLASS = PrimitiveType("class")
COMPONENT = PrimitiveType("component")
MODULE = PrimitiveType("module")

# Convenience instances for common generic types
ANY_LIST = ListType(ANY)
ANY_DICT = DictType(ANY, ANY)
