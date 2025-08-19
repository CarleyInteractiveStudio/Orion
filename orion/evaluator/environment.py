from __future__ import annotations
from typing import Optional
from orion.object.object import Object

class Environment:
    def __init__(self, outer: Optional[Environment] = None):
        self.store: dict[str, Object] = {}
        self.outer = outer

    def get(self, name: str) -> Optional[Object]:
        val = self.store.get(name)
        if val is None and self.outer is not None:
            return self.outer.get(name)
        return val

    def set(self, name: str, val: Object) -> Object:
        self.store[name] = val
        return val

def new_environment() -> Environment:
    return Environment()

def new_enclosed_environment(outer: Environment) -> Environment:
    return Environment(outer=outer)
