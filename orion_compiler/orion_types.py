from enum import Enum, auto

class OrionType(Enum):
    ANY = auto()
    NIL = auto()
    BOOL = auto()
    NUMBER = auto()
    STRING = auto()
    FUNCTION = auto()
    COMPONENT = auto()
    MODULE = auto()
