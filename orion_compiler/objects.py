from bytecode import Chunk
from typing import Callable, Any
from tokens import Token

from typing import List

class OrionObject:
    """Base class for all runtime objects in Orion."""
    pass

class OrionList(OrionObject):
    """Represents a list in Orion."""
    def __init__(self, elements: List[Any]):
        self.elements = elements

    def __str__(self) -> str:
        return f"[{', '.join(map(str, self.elements))}]"

class OrionDict(OrionObject):
    """Represents a dictionary (hash map) in Orion."""
    def __init__(self, pairs: dict):
        self.pairs = pairs

    def __str__(self) -> str:
        items = [f'"{k}": {v}' for k, v in self.pairs.items()]
        return f"{{{', '.join(items)}}}"

class OrionNativeFunction(OrionObject):
    """A wrapper for native Python functions exposed to Orion."""
    def __init__(self, arity: int, func: Callable):
        self.arity = arity
        self.func = func

    def __str__(self) -> str:
        return "<native fn>"

class OrionCompiledFunction(OrionObject):
    """Represents a compiled function."""
    def __init__(self, arity: int, chunk: Chunk, name: str):
        self.arity = arity
        self.chunk = chunk
        self.name = name

    def __str__(self) -> str:
        return f"<fn {self.name}>"

class OrionInstance(OrionObject):
    """Represents an instance of a component or a module namespace."""
    def __init__(self):
        self.fields = {}

    def get(self, name: Token):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]
        # In the future, this could raise an error.
        # For now, we return None for undefined properties.
        return None

    def set(self, name: Token, value: Any):
        self.fields[name.lexeme] = value

    def __str__(self):
        return "<instance>"
