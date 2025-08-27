from . bytecode import Chunk
from typing import Callable, Any
from . tokens import Token

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

class OrionClass(OrionObject):
    """Represents a class definition at runtime."""
    def __init__(self, name: str, superclass: 'OrionClass' = None):
        self.name = name
        self.methods = {}
        self.superclass = superclass

    def __str__(self) -> str:
        return f"<class {self.name}>"

class OrionComponentDef(OrionObject):
    """Represents a component's definition (its 'class')."""
    def __init__(self, name: str, properties: List['PropertyDecl']):
        self.name = name
        self.properties = properties
        self.methods: dict = {}

    def __str__(self) -> str:
        return f"<component {self.name}>"

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

class OrionComponentInstance(OrionInstance):
    """Represents an instance of a component."""
    def __init__(self, definition: OrionComponentDef):
        super().__init__()
        self.definition = definition
        self.dirty = True # Start as dirty to trigger initial render

    def __str__(self):
        return f"<{self.definition.name} instance>"

class OrionClassInstance(OrionInstance):
    """Represents an instance of a user-defined class."""
    def __init__(self, klass: OrionClass):
        super().__init__()
        self.klass = klass

    def __str__(self):
        return f"<{self.klass.name} instance>"

class OrionBoundMethod(OrionObject):
    """A method bound to a specific receiver instance."""
    def __init__(self, receiver: OrionInstance, method: OrionCompiledFunction):
        self.receiver = receiver
        self.method = method

    def __str__(self):
        return str(self.method)

class StateProxy(OrionInstance):
    """
    A wrapper for a component's state dictionary that marks the component
    as dirty when a property is set.
    """
    def __init__(self, owner: OrionComponentInstance, initial_state: dict):
        super().__init__()
        self.owner = owner
        self.fields = initial_state

    def set(self, name: Token, value: Any):
        """Sets a value and marks the owner component as dirty."""
        super().set(name, value)
        self.owner.dirty = True
        print(f"DEBUG: State set, {self.owner.definition.name} is now dirty.")
