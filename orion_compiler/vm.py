from bytecode import Chunk, OpCode

# A simple enum for interpreter results
class InterpretResult:
    OK = 0
    COMPILE_ERROR = 1
    RUNTIME_ERROR = 2

class VM:
    """
    The Virtual Machine runs the bytecode compiled by the Compiler.
    It is a stack-based VM.
    """
    def __init__(self):
        self.chunk: Chunk = None
        self.ip: int = 0 # Instruction Pointer
        self.stack: list = []
        self.globals: dict = {}

    def interpret(self, chunk: Chunk) -> InterpretResult:
        self.chunk = chunk
        self.ip = 0
        self.last_value = None

        result = self._run()

        # Return the last value on the stack as the result of the script
        return result, self.last_value

    def _run(self) -> InterpretResult:
        while True:
            instruction = OpCode(self._read_byte())

            if instruction == OpCode.OP_RETURN:
                if self.stack:
                    self.last_value = self.pop()
                return InterpretResult.OK

            elif instruction == OpCode.OP_CONSTANT:
                constant_idx = self._read_byte()
                constant = self._read_constant(constant_idx)
                self.push(constant)

            elif instruction == OpCode.OP_NEGATE:
                # Type checking should happen here at runtime for a dynamic lang
                # or have been done by a static type checker.
                value = self.pop()
                self.push(-value)

            elif instruction == OpCode.OP_ADD: self._binary_op(lambda a, b: a + b)
            elif instruction == OpCode.OP_SUBTRACT: self._binary_op(lambda a, b: a - b)
            elif instruction == OpCode.OP_MULTIPLY: self._binary_op(lambda a, b: a * b)
            elif instruction == OpCode.OP_DIVIDE: self._binary_op(lambda a, b: a / b)

            elif instruction == OpCode.OP_EQUAL: self._binary_op(lambda a, b: a == b)
            elif instruction == OpCode.OP_GREATER: self._binary_op(lambda a, b: a > b)
            elif instruction == OpCode.OP_LESS: self._binary_op(lambda a, b: a < b)

            elif instruction == OpCode.OP_NOT:
                self.push(not self.pop()) # Simple boolean not

            elif instruction == OpCode.OP_TRUE: self.push(True)
            elif instruction == OpCode.OP_FALSE: self.push(False)
            elif instruction == OpCode.OP_NIL: self.push(None)

            elif instruction == OpCode.OP_POP:
                self.pop()

            elif instruction == OpCode.OP_DEFINE_GLOBAL:
                name = self._read_constant(self._read_byte())
                self.globals[name] = self.peek(0)
                self.pop()

            elif instruction == OpCode.OP_GET_GLOBAL:
                name = self._read_constant(self._read_byte())
                if name not in self.globals:
                    # A real VM would have a better error reporting system
                    print(f"RuntimeError: Undefined variable '{name}'.")
                    return InterpretResult.RUNTIME_ERROR
                self.push(self.globals[name])

            elif instruction == OpCode.OP_SET_GLOBAL:
                name = self._read_constant(self._read_byte())
                if name not in self.globals:
                    print(f"RuntimeError: Undefined variable '{name}'.")
                    return InterpretResult.RUNTIME_ERROR
                self.globals[name] = self.peek(0)

    # --- Helper Methods ---

    def _read_byte(self) -> int:
        byte = self.chunk.code[self.ip]
        self.ip += 1
        return byte

    def _read_constant(self, index: int):
        return self.chunk.constants[index]

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        return self.stack.pop()

    def peek(self, distance: int):
        return self.stack[-1 - distance]

    def _binary_op(self, op_func):
        # A real VM would have runtime type checks here.
        b = self.pop()
        a = self.pop()
        self.push(op_func(a, b))
