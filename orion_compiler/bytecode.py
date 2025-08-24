from enum import IntEnum
from typing import List, Any

class OpCode(IntEnum):
    """
    Defines the instruction set for the Orion Virtual Machine.
    Each instruction has a 1-byte operation code.
    """
    # --- Constants and Literals ---
    OP_CONSTANT = 0     # Pushes a constant from the constant pool. Operand: 1-byte index.

    # --- Literals ---
    OP_NIL = 1
    OP_TRUE = 2
    OP_FALSE = 3

    # --- Stack Operations ---
    OP_POP = 4

    # --- Unary Operations ---
    OP_NEGATE = 5
    OP_NOT = 6

    # --- Binary Operations ---
    OP_ADD = 7
    OP_SUBTRACT = 8
    OP_MULTIPLY = 9
    OP_DIVIDE = 10

    # --- Comparison ---
    OP_EQUAL = 11
    OP_GREATER = 12
    OP_LESS = 13

    # --- Variables ---
    OP_DEFINE_GLOBAL = 14
    OP_GET_GLOBAL = 15
    OP_SET_GLOBAL = 16
    OP_GET_LOCAL = 17
    OP_SET_LOCAL = 18

    # --- Jumps ---
    OP_JUMP_IF_FALSE = 19
    OP_JUMP = 20
    OP_LOOP = 21

    # --- Functions ---
    OP_CALL = 22
    OP_RETURN = 23

    # --- Modules ---
    OP_USE = 24

    # --- Properties ---
    OP_GET_PROPERTY = 25
    OP_SET_PROPERTY = 26

    # --- Data Structures ---
    OP_BUILD_LIST = 27
    OP_GET_SUBSCRIPT = 28
    OP_SET_SUBSCRIPT = 29
    OP_BUILD_DICT = 30

    # --- End of Execution ---
    # OP_RETURN now serves this purpose


class Chunk:
    """
    A chunk of bytecode representing a piece of compiled code.
    It contains the instructions, a constant pool, and line number information.
    """
    def __init__(self):
        self.code: bytearray = bytearray()
        self.constants: List[Any] = []
        self.lines: List[int] = []

    def write(self, byte: int, line: int):
        """
        Appends a byte to the chunk.
        Args:
            byte: The byte to append (can be an OpCode or an operand).
            line: The source code line number corresponding to this instruction.
        """
        self.code.append(byte)
        self.lines.append(line)

    def add_constant(self, value: Any) -> int:
        """
        Adds a value to the constant pool.
        Returns:
            The index of the added constant.
        """
        self.constants.append(value)
        return len(self.constants) - 1
