from bytecode import Chunk, OpCode
from objects import OrionCompiledFunction
from dataclasses import dataclass
from typing import Any

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

    def interpret(self, main_function: OrionCompiledFunction) -> InterpretResult:
        frame = CallFrame(main_function, 0, 0)
        self.stack.append(main_function) # Push the main function itself onto the stack
        self.frames.append(frame)

        return self._run()

    def _run(self) -> (InterpretResult, Any):
        frame = self.frames[-1]

        def read_byte():
            byte = frame.function.chunk.code[frame.ip]
            frame.ip += 1
            return byte

        def read_short():
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
                    self.pop() # Pop script function
                    return InterpretResult.OK, result

                self.stack = self.stack[:frame.slots_offset]
                self.push(result)
                frame = self.frames[-1]

            elif instruction == OpCode.OP_CALL:
                arg_count = read_byte()
                callee = self.peek(arg_count)
                if isinstance(callee, OrionCompiledFunction):
                    if arg_count != callee.arity:
                        print(f"RuntimeError: Expected {callee.arity} arguments but got {arg_count}.")
                        return InterpretResult.RUNTIME_ERROR, None

                    frame = CallFrame(callee, 0, len(self.stack) - arg_count - 1)
                    self.frames.append(frame)
                else:
                    print("RuntimeError: Can only call functions.")
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

    def _is_falsey(self, value) -> bool:
        return value is None or (isinstance(value, bool) and not value)

    def push(self, value): self.stack.append(value)
    def pop(self): return self.stack.pop()
    def peek(self, distance: int): return self.stack[-1 - distance]
    def _binary_op(self, op_func):
        b = self.pop()
        a = self.pop()
        self.push(op_func(a, b))
