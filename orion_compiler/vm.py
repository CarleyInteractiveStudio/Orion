from bytecode import Chunk, OpCode
from objects import OrionCompiledFunction, OrionNativeFunction, OrionComponentDef, OrionComponentInstance, OrionBoundMethod, OrionInstance, OrionList, OrionDict, StateProxy
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
        self.draw_commands: list = []
        self._init_io_module()
        self._init_draw_module()

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

    def _init_draw_module(self):
        """Initializes the native 'draw' module."""
        def native_draw_box(options):
            if not isinstance(options, OrionDict):
                print("RuntimeError: draw.box requires a dictionary argument.")
                return None

            props = options.pairs
            self.draw_commands.append({
                "command": "box",
                "x": props.get("x", 0),
                "y": props.get("y", 0),
                "width": props.get("width", 10),
                "height": props.get("height", 5),
                "color": props.get("color", "#FFFFFF"),
            })
            return None

        def native_draw_text(options):
            if not isinstance(options, OrionDict):
                print("RuntimeError: draw.text requires a dictionary argument.")
                return None

            props = options.pairs
            self.draw_commands.append({
                "command": "text",
                "x": props.get("x", 0),
                "y": props.get("y", 0),
                "text": props.get("text", ""),
                "color": props.get("color", "#FFFFFF"),
                "fontSize": props.get("fontSize", 12),
            })
            return None

        draw_module = {
            "box": OrionNativeFunction(1, native_draw_box),
            "text": OrionNativeFunction(1, native_draw_text),
        }
        self.native_modules["draw"] = draw_module

    def interpret(self, main_function: OrionCompiledFunction) -> InterpretResult:
        self.stack = []
        self.frames = []
        self.stack.append(main_function)
        frame = CallFrame(main_function, 0, 0)
        self.frames.append(frame)
        return self._run()

    def call_method_on_instance(self, instance: OrionComponentInstance, method_name: str):
        """Finds and executes a method on a component instance."""
        if method_name not in instance.definition.methods:
            return # Or raise an error

        method_code = instance.definition.methods[method_name]

        # Manually set up the call on the stack
        bound_method = OrionBoundMethod(instance, method_code)
        self.push(bound_method)

        # Set up a new call frame and run it
        self._call_value(bound_method, 0)

        # Run the VM until this new call frame is complete, and return the result.
        result, last_value = self._run()
        return last_value

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
                if not self._call_value(callee, arg_count):
                    return InterpretResult.RUNTIME_ERROR, None

                # After a successful call, the frame might have changed.
                frame = self.frames[-1]

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

                # Module resolution order: stdlib -> current directory
                possible_paths = [
                    f"orion_compiler/stdlib/{module_name}.orion",
                    f"orion_compiler/{module_name}.orion"
                ]

                source = None
                for path in possible_paths:
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            source = f.read()
                        break

                if source is None:
                    print(f"RuntimeError: Module '{module_name}' not found.")
                    return InterpretResult.RUNTIME_ERROR, None

                from orion import Orion
                module_runner = Orion()
                module_runner.run(source)
                namespace = OrionInstance()
                namespace.fields = module_runner.vm.globals
                self.push(namespace)

            elif instruction == OpCode.OP_GET_PROPERTY:
                instance = self.peek(0)
                name = read_constant()

                if isinstance(instance, OrionComponentInstance):
                    # First, check for a field with that name. Fields shadow methods.
                    if name in instance.fields:
                        self.pop() # Pop instance
                        self.push(instance.fields[name])
                        continue
                    # If no field, check for a method.
                    if name in instance.definition.methods:
                        method = instance.definition.methods[name]
                        bound_method = OrionBoundMethod(instance, method)
                        self.pop() # Pop instance
                        self.push(bound_method)
                        continue

                    print(f"RuntimeError: Undefined property '{name}' on component '{instance.definition.name}'.")
                    return InterpretResult.RUNTIME_ERROR, None

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

                # Fallback for other instance types like modules
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

    def _call_value(self, callee: Any, arg_count: int) -> bool:
        """Helper to call a value from the stack."""
        if isinstance(callee, OrionNativeFunction):
            if callee.arity is not None and arg_count != callee.arity:
                print(f"RuntimeError: Expected {callee.arity} arguments but got {arg_count}.")
                return False
            args = self.stack[-arg_count:]
            self.stack = self.stack[:-arg_count-1]
            result = callee.func(*args)
            self.push(result)
            return True
        elif isinstance(callee, OrionCompiledFunction):
            if arg_count != callee.arity:
                print(f"RuntimeError: Expected {callee.arity} arguments but got {arg_count}.")
                return False
            frame = CallFrame(callee, 0, len(self.stack) - arg_count - 1)
            self.frames.append(frame)
            return True
        elif isinstance(callee, OrionComponentDef):
            # Arity check: 0 or 1 arguments (the props dictionary)
            if arg_count > 1:
                print(f"RuntimeError: Component '{callee.name}' constructor takes 0 or 1 arguments, but got {arg_count}.")
                return False

            props = {}
            if arg_count == 1:
                props_arg = self.peek(0)
                if not isinstance(props_arg, OrionDict):
                    print(f"RuntimeError: Component constructor argument must be a dictionary.")
                    return False
                props = props_arg.pairs
                self.pop() # Pop the props dict

            definition = self.stack.pop() # Pop the component definition
            instance = OrionComponentInstance(definition)

            # 1. Initialize with default values from the component definition
            for prop_node in definition.properties:
                prop_name = prop_node.name.lexeme
                default_value = None
                if len(prop_node.values) == 1:
                    default_value = prop_node.values[0].literal
                instance.fields[prop_name] = default_value

            # 2. Override with any passed-in props
            for key, value in props.items():
                instance.fields[key] = value

            # 3. If a 'state' property exists and is a dictionary, wrap it in a proxy.
            if "state" in instance.fields and isinstance(instance.fields["state"], OrionDict):
                state_dict = instance.fields["state"]
                instance.fields["state"] = StateProxy(instance, state_dict.pairs)

            self.push(instance)
            return True
        elif isinstance(callee, OrionBoundMethod):
            if arg_count != callee.method.arity:
                print(f"RuntimeError: Method '{callee.method.name}' expected {callee.method.arity} arguments but got {arg_count}.")
                return False
            self.stack[-1 - arg_count] = callee.receiver
            frame = CallFrame(callee.method, 0, len(self.stack) - arg_count - 1)
            self.frames.append(frame)
            return True
        else:
            print(f"RuntimeError: Can only call functions and components, not {type(callee).__name__}.")
            return False

    def _is_falsey(self, value) -> bool:
        return value is None or (isinstance(value, bool) and not value)

    def push(self, value): self.stack.append(value)
    def pop(self): return self.stack.pop()
    def peek(self, distance: int): return self.stack[-1 - distance]
    def _binary_op(self, op_func):
        b = self.pop()
        a = self.pop()
        self.push(op_func(a, b))
