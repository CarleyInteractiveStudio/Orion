from bytecode import Chunk, OpCode
from objects import OrionCompiledFunction, OrionNativeFunction, OrionComponentDef, OrionComponentInstance, OrionInstance, OrionList, OrionDict
from tokens import Token
from dataclasses import dataclass
from typing import Any
import time
import os

@dataclass
class CallFrame:
    function: OrionCompiledFunction
    ip: int
    slots_offset: int

class InterpretResult:
    OK = 0
    COMPILE_ERROR = 1
    RUNTIME_ERROR = 2

class VM:
    def __init__(self):
        self.frames: list[CallFrame] = []
        self.stack: list = []
        self.globals: dict = {}

        # --- Native Functions ---
        self._define_native("clock", 0, lambda: time.time())
        def native_print(*args):
            print(*[str(arg) for arg in args])
            return None
        self._define_native("print", None, native_print) # Variadic

        # --- Native Modules ---
        self.native_modules: dict = {}
        self._init_io_module()

    def _define_native(self, name: str, arity: int, func):
        self.globals[name] = OrionNativeFunction(arity, func)

    def _init_io_module(self):
        def native_io_read(path):
            try:
                with open(path, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                return None

        def native_io_write(path, content):
            with open(path, 'w') as f:
                f.write(str(content))
            return None

        def native_io_append(path, content):
            with open(path, 'a') as f:
                f.write(str(content))
            return None

        def native_io_exists(path):
            return os.path.exists(path)

        io_module = {
            "read": OrionNativeFunction(1, native_io_read),
            "write": OrionNativeFunction(2, native_io_write),
            "append": OrionNativeFunction(2, native_io_append),
            "exists": OrionNativeFunction(1, native_io_exists),
        }
        self.native_modules["io"] = io_module

    def interpret(self, main_function: OrionCompiledFunction) -> InterpretResult:
        self.stack = []
        self.frames = []
        self.stack.append(main_function)
        frame = CallFrame(main_function, 0, 0)
        self.frames.append(frame)
        return self._run()

    def _run(self) -> (InterpretResult, Any):
        frame = self.frames[-1]

        def read_byte():
            nonlocal frame
            byte = frame.function.chunk.code[frame.ip]
            frame.ip += 1
            return byte

        def read_short():
            nonlocal frame
            frame.ip += 2
            return (frame.function.chunk.code[frame.ip - 2] << 8) | frame.function.chunk.code[frame.ip - 1]

        def read_constant():
            return frame.function.chunk.constants[read_byte()]

        while True:
            instruction = OpCode(read_byte())

            if instruction == OpCode.OP_RETURN:
                result = self.pop()
                self.frames.pop()
                if not self.frames:
                    return InterpretResult.OK, result
                self.stack = self.stack[:frame.slots_offset]
                self.push(result)
                frame = self.frames[-1]

            elif instruction == OpCode.OP_CALL:
                arg_count = read_byte()
                callee = self.peek(arg_count)
                if isinstance(callee, OrionNativeFunction):
                    if callee.arity is not None and arg_count != callee.arity:
                        print(f"RuntimeError: Expected {callee.arity} arguments but got {arg_count}.")
                        return InterpretResult.RUNTIME_ERROR, None
                    args = self.stack[-arg_count:]
                    self.stack = self.stack[:-arg_count-1]
                    result = callee.func(*args)
                    self.push(result)
                elif isinstance(callee, OrionCompiledFunction):
                    if arg_count != callee.arity:
                        print(f"RuntimeError: Expected {callee.arity} arguments but got {arg_count}.")
                        return InterpretResult.RUNTIME_ERROR, None
                    frame = CallFrame(callee, 0, len(self.stack) - arg_count - 1)
                    self.frames.append(frame)
                elif isinstance(callee, OrionComponentDef):
                    if arg_count != 0:
                        print(f"RuntimeError: Component '{callee.name}' constructor takes no arguments, but got {arg_count}.")
                        return InterpretResult.RUNTIME_ERROR, None

                    # Pop the component definition
                    definition = self.stack.pop()
                    instance = OrionComponentInstance(definition)

                    # Initialize properties with default values
                    for prop_node in definition.properties:
                        prop_name = prop_node.name.lexeme
                        default_value = None
                        if len(prop_node.values) == 1:
                            # The lexer stores the literal value in the token
                            default_value = prop_node.values[0].literal
                        instance.fields[prop_name] = default_value

                    self.push(instance)
                else:
                    print(f"RuntimeError: Can only call functions and components, not {type(callee).__name__}.")
                    return InterpretResult.RUNTIME_ERROR, None

            elif instruction == OpCode.OP_CONSTANT: self.push(read_constant())
            elif instruction == OpCode.OP_NEGATE: self.push(-self.pop())
            elif instruction == OpCode.OP_ADD: self._binary_op(lambda a, b: a + b)
            elif instruction == OpCode.OP_SUBTRACT: self._binary_op(lambda a, b: a - b)
            elif instruction == OpCode.OP_MULTIPLY: self._binary_op(lambda a, b: a * b)
            elif instruction == OpCode.OP_DIVIDE: self._binary_op(lambda a, b: a / b)
            elif instruction == OpCode.OP_EQUAL: self._binary_op(lambda a, b: a == b)
            elif instruction == OpCode.OP_GREATER: self._binary_op(lambda a, b: a > b)
            elif instruction == OpCode.OP_LESS: self._binary_op(lambda a, b: a < b)
            elif instruction == OpCode.OP_NOT: self.push(not self._is_falsey(self.pop()))
            elif instruction == OpCode.OP_TRUE: self.push(True)
            elif instruction == OpCode.OP_FALSE: self.push(False)
            elif instruction == OpCode.OP_NIL: self.push(None)
            elif instruction == OpCode.OP_POP: self.pop()

            elif instruction == OpCode.OP_DEFINE_GLOBAL:
                name = read_constant()
                self.globals[name] = self.peek(0)
                self.pop()
            elif instruction == OpCode.OP_GET_GLOBAL:
                name = read_constant()
                if name not in self.globals:
                    print(f"RuntimeError: Undefined variable '{name}'.")
                    return InterpretResult.RUNTIME_ERROR, None
                self.push(self.globals[name])
            elif instruction == OpCode.OP_SET_GLOBAL:
                name = read_constant()
                if name not in self.globals:
                    print(f"RuntimeError: Undefined variable '{name}'.")
                    return InterpretResult.RUNTIME_ERROR, None
                self.globals[name] = self.peek(0)

            elif instruction == OpCode.OP_GET_LOCAL:
                slot = read_byte()
                self.push(self.stack[frame.slots_offset + slot])
            elif instruction == OpCode.OP_SET_LOCAL:
                slot = read_byte()
                self.stack[frame.slots_offset + slot] = self.peek(0)

            elif instruction == OpCode.OP_JUMP:
                offset = read_short()
                frame.ip += offset
            elif instruction == OpCode.OP_JUMP_IF_FALSE:
                offset = read_short()
                if self._is_falsey(self.peek(0)):
                    frame.ip += offset
            elif instruction == OpCode.OP_LOOP:
                offset = read_short()
                frame.ip -= offset

            elif instruction == OpCode.OP_USE:
                module_name = read_constant()
                if module_name in self.native_modules:
                    namespace = OrionInstance()
                    namespace.fields = self.native_modules[module_name]
                    self.push(namespace)
                    continue
                file_path = f"orion_compiler/{module_name}.orion"
                from orion import Orion
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        source = f.read()
                except FileNotFoundError:
                    print(f"RuntimeError: Module file not found: '{file_path}'")
                    return InterpretResult.RUNTIME_ERROR, None
                module_runner = Orion()
                module_runner.run(source)
                namespace = OrionInstance()
                namespace.fields = module_runner.vm.globals
                self.push(namespace)

            elif instruction == OpCode.OP_GET_PROPERTY:
                instance = self.peek(0)
                name = read_constant()
                if isinstance(instance, OrionList):
                    if name == "length":
                        self.pop()
                        self.push(len(instance.elements))
                        continue
                    else:
                        print(f"RuntimeError: Type 'list' has no property '{name}'.")
                        return InterpretResult.RUNTIME_ERROR, None
                if not isinstance(instance, OrionInstance):
                    print("RuntimeError: Only instances and lists have properties.")
                    return InterpretResult.RUNTIME_ERROR, None
                value = instance.get(Token(None, name, None, 0))
                self.pop()
                self.push(value)

            elif instruction == OpCode.OP_SET_PROPERTY:
                instance = self.peek(1)
                if isinstance(instance, OrionList):
                    print("RuntimeError: Cannot set properties on a list.")
                    return InterpretResult.RUNTIME_ERROR, None
                if not isinstance(instance, OrionInstance):
                    print("RuntimeError: Only instances have properties.")
                    return InterpretResult.RUNTIME_ERROR, None
                name = read_constant()
                value = self.peek(0)
                instance.set(Token(None, name, None, 0), value)
                self.pop()
                self.pop()
                self.push(value)

            elif instruction == OpCode.OP_BUILD_LIST:
                item_count = read_byte()
                elements = self.stack[-item_count:]
                self.stack = self.stack[:-item_count]
                list_obj = OrionList(elements)
                self.push(list_obj)

            elif instruction == OpCode.OP_GET_SUBSCRIPT:
                index = self.pop()
                collection = self.pop()
                if isinstance(collection, OrionList):
                    if not isinstance(index, int):
                        print(f"RuntimeError: List index must be an integer, not {type(index).__name__}.")
                        return InterpretResult.RUNTIME_ERROR, None
                    try:
                        self.push(collection.elements[index])
                    except IndexError:
                        print(f"RuntimeError: List index {index} out of range.")
                        return InterpretResult.RUNTIME_ERROR, None
                elif isinstance(collection, OrionDict):
                    if not isinstance(index, (str, int, bool, type(None))):
                         print(f"RuntimeError: Dictionary key must be a valid hashable type.")
                         return InterpretResult.RUNTIME_ERROR, None
                    self.push(collection.pairs.get(index))
                else:
                    print("RuntimeError: Object is not subscriptable.")
                    return InterpretResult.RUNTIME_ERROR, None

            elif instruction == OpCode.OP_SET_SUBSCRIPT:
                value = self.pop()
                index = self.pop()
                collection = self.pop()
                if isinstance(collection, OrionList):
                    if not isinstance(index, int):
                        print(f"RuntimeError: List index must be an integer.")
                        return InterpretResult.RUNTIME_ERROR, None
                    try:
                        collection.elements[index] = value
                        self.push(value)
                    except IndexError:
                        print(f"RuntimeError: List index {index} out of range.")
                        return InterpretResult.RUNTIME_ERROR, None
                elif isinstance(collection, OrionDict):
                    if not isinstance(index, (str, int, bool, type(None))):
                         print(f"RuntimeError: Dictionary key must be a valid hashable type.")
                         return InterpretResult.RUNTIME_ERROR, None
                    collection.pairs[index] = value
                    self.push(value)
                else:
                    print("RuntimeError: Object is not subscriptable.")
                    return InterpretResult.RUNTIME_ERROR, None

            elif instruction == OpCode.OP_BUILD_DICT:
                pair_count = read_byte()
                pairs = {}
                for _ in range(pair_count):
                    value = self.pop()
                    key = self.pop()
                    pairs[key] = value
                dict_obj = OrionDict(pairs)
                self.push(dict_obj)

    def _is_falsey(self, value) -> bool:
        return value is None or (isinstance(value, bool) and not value)

    def push(self, value): self.stack.append(value)
    def pop(self): return self.stack.pop()
    def peek(self, distance: int): return self.stack[-1 - distance]
    def _binary_op(self, op_func):
        b = self.pop()
        a = self.pop()
        self.push(op_func(a, b))
