import pytest
from orion_compiler.compiler import compile, TypeAnalyzer
from orion_compiler.bytecode import OpCode

def compile_and_get_bytecode(source):
    type_analyzer = TypeAnalyzer()

    # Run the type analyzer
    from orion_compiler.lexer import Lexer
    from orion_compiler.parser import Parser
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()
    parser = Parser(tokens)
    statements = parser.parse()
    type_analyzer.analyze(statements)

    # Compile
    result = compile(source, type_analyzer)
    assert result is not None, "Compilation failed"
    return result.chunk.code

def test_number_addition_bytecode():
    bytecode = compile_and_get_bytecode("var a: number = 1; var b: number = 2; var c = a + b;")
    assert OpCode.OP_ADD_NUMBER in bytecode
    assert OpCode.OP_ADD not in bytecode

def test_string_concatenation_bytecode():
    bytecode = compile_and_get_bytecode('var a: string = "hello"; var b: string = " world"; var c = a + b;')
    assert OpCode.OP_ADD_STRING in bytecode
    assert OpCode.OP_ADD not in bytecode

def test_any_addition_bytecode():
    bytecode = compile_and_get_bytecode("var a: any = 1; var b: any = 2; var c = a + b;")
    assert OpCode.OP_ADD in bytecode
    assert OpCode.OP_ADD_NUMBER not in bytecode
    assert OpCode.OP_ADD_STRING not in bytecode

def test_number_subtraction_bytecode():
    bytecode = compile_and_get_bytecode("var a: number = 2; var b: number = 1; var c = a - b;")
    assert OpCode.OP_SUBTRACT_NUMBER in bytecode
    assert OpCode.OP_SUBTRACT not in bytecode

def test_number_multiplication_bytecode():
    bytecode = compile_and_get_bytecode("var a: number = 2; var b: number = 3; var c = a * b;")
    assert OpCode.OP_MULTIPLY_NUMBER in bytecode
    assert OpCode.OP_MULTIPLY not in bytecode

def test_number_division_bytecode():
    bytecode = compile_and_get_bytecode("var a: number = 6; var b: number = 3; var c = a / b;")
    assert OpCode.OP_DIVIDE_NUMBER in bytecode
    assert OpCode.OP_DIVIDE not in bytecode

def test_number_greater_than_bytecode():
    bytecode = compile_and_get_bytecode("var a: number = 2; var b: number = 1; var c = a > b;")
    assert OpCode.OP_GREATER_NUMBER in bytecode
    assert OpCode.OP_GREATER not in bytecode

def test_number_less_than_bytecode():
    bytecode = compile_and_get_bytecode("var a: number = 1; var b: number = 2; var c = a < b;")
    assert OpCode.OP_LESS_NUMBER in bytecode
    assert OpCode.OP_LESS not in bytecode

def test_number_equality_bytecode():
    bytecode = compile_and_get_bytecode("var a: number = 2; var b: number = 2; var c = a == b;")
    assert OpCode.OP_EQUAL_NUMBER in bytecode
    assert OpCode.OP_EQUAL not in bytecode
