from bytecode import Chunk, OpCode

def disassemble_chunk(chunk: Chunk, name: str):
    """Prints a human-readable representation of a chunk of bytecode."""
    print(f"== {name} ==")
    offset = 0
    while offset < len(chunk.code):
        offset = disassemble_instruction(chunk, offset)

def disassemble_instruction(chunk: Chunk, offset: int) -> int:
    """Prints one instruction and returns the offset of the next one."""
    print(f"{offset:04d} ", end="")

    if offset > 0 and chunk.lines[offset] == chunk.lines[offset - 1]:
        print("   | ", end="")
    else:
        print(f"{chunk.lines[offset]:4d} ", end="")

    instruction = OpCode(chunk.code[offset])

    # These are helper functions for different instruction formats
    def simple_instruction(name, offset):
        print(f"{name}")
        return offset + 1

    def constant_instruction(name, chunk, offset):
        constant_idx = chunk.code[offset + 1]
        constant_val = chunk.constants[constant_idx]
        print(f"{name:<16} {constant_idx:4d} '{constant_val}'")
        return offset + 2

    def byte_instruction(name, chunk, offset):
        slot = chunk.code[offset + 1]
        print(f"{name:<16} {slot:4d}")
        return offset + 2

    def jump_instruction(name, sign, chunk, offset):
        jump = (chunk.code[offset + 1] << 8) | chunk.code[offset + 2]
        print(f"{name:<16} {offset:4d} -> {offset + 3 + sign * jump}")
        return offset + 3

    if instruction == OpCode.OP_RETURN:
        return simple_instruction("OP_RETURN", offset)
    elif instruction == OpCode.OP_CONSTANT:
        return constant_instruction("OP_CONSTANT", chunk, offset)
    elif instruction == OpCode.OP_NEGATE:
        return simple_instruction("OP_NEGATE", offset)
    elif instruction == OpCode.OP_ADD:
        return simple_instruction("OP_ADD", offset)
    elif instruction == OpCode.OP_SUBTRACT:
        return simple_instruction("OP_SUBTRACT", offset)
    elif instruction == OpCode.OP_MULTIPLY:
        return simple_instruction("OP_MULTIPLY", offset)
    elif instruction == OpCode.OP_DIVIDE:
        return simple_instruction("OP_DIVIDE", offset)
    elif instruction == OpCode.OP_POP:
        return simple_instruction("OP_POP", offset)
    elif instruction == OpCode.OP_DEFINE_GLOBAL:
        return constant_instruction("OP_DEFINE_GLOBAL", chunk, offset)
    elif instruction == OpCode.OP_GET_GLOBAL:
        return constant_instruction("OP_GET_GLOBAL", chunk, offset)
    elif instruction == OpCode.OP_SET_GLOBAL:
        return constant_instruction("OP_SET_GLOBAL", chunk, offset)
    elif instruction == OpCode.OP_GET_LOCAL:
        return byte_instruction("OP_GET_LOCAL", chunk, offset)
    elif instruction == OpCode.OP_SET_LOCAL:
        return byte_instruction("OP_SET_LOCAL", chunk, offset)
    elif instruction == OpCode.OP_JUMP:
        return jump_instruction("OP_JUMP", 1, chunk, offset)
    elif instruction == OpCode.OP_JUMP_IF_FALSE:
        return jump_instruction("OP_JUMP_IF_FALSE", 1, chunk, offset)
    elif instruction == OpCode.OP_LOOP:
        return jump_instruction("OP_LOOP", -1, chunk, offset)
    elif instruction == OpCode.OP_GREATER:
        return simple_instruction("OP_GREATER", offset)
    elif instruction == OpCode.OP_LESS:
        return simple_instruction("OP_LESS", offset)
    elif instruction == OpCode.OP_EQUAL:
        return simple_instruction("OP_EQUAL", offset)
    elif instruction == OpCode.OP_NOT:
        return simple_instruction("OP_NOT", offset)
    elif instruction == OpCode.OP_NIL:
        return simple_instruction("OP_NIL", offset)
    elif instruction == OpCode.OP_TRUE:
        return simple_instruction("OP_TRUE", offset)
    elif instruction == OpCode.OP_FALSE:
        return simple_instruction("OP_FALSE", offset)
    elif instruction == OpCode.OP_GET_PROPERTY:
        return constant_instruction("OP_GET_PROPERTY", chunk, offset)
    elif instruction == OpCode.OP_SET_PROPERTY:
        return constant_instruction("OP_SET_PROPERTY", chunk, offset)
    elif instruction == OpCode.OP_BUILD_LIST:
        return byte_instruction("OP_BUILD_LIST", chunk, offset)
    elif instruction == OpCode.OP_GET_SUBSCRIPT:
        return simple_instruction("OP_GET_SUBSCRIPT", offset)
    elif instruction == OpCode.OP_SET_SUBSCRIPT:
        return simple_instruction("OP_SET_SUBSCRIPT", offset)
    elif instruction == OpCode.OP_BUILD_DICT:
        return byte_instruction("OP_BUILD_DICT", chunk, offset)

    else:
        print(f"Unknown opcode {instruction}")
        return offset + 1
