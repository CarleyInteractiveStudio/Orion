from bytecode import Chunk

class OrionObject:
    """Base class for all runtime objects in Orion."""
    pass

class OrionCompiledFunction(OrionObject):
    """Represents a compiled function."""
    def __init__(self, arity: int, chunk: Chunk, name: str):
        self.arity = arity
        self.chunk = chunk
        self.name = name

    def __str__(self) -> str:
        return f"<fn {self.name}>"
