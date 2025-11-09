import pytest
from orion_compiler.compiler import compile, TypeAnalyzer
from orion_compiler.bytecode import OpCode

def test_number_addition_bytecode():
    source = "var a: number = 1; var b: number = 2; var c = a + b;"
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

    # Check for the specific opcode
    assert OpCode.OP_ADD_NUMBER in result.chunk.code, "OP_ADD_NUMBER not found in bytecode"
    assert OpCode.OP_ADD not in result.chunk.code, "Generic OP_ADD should not be present"

def test_string_concatenation_bytecode():
    source = 'var a: string = "hello"; var b: string = " world"; var c = a + b;'
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

    # Check for the specific opcode
    assert OpCode.OP_ADD_STRING in result.chunk.code, "OP_ADD_STRING not found in bytecode"
    assert OpCode.OP_ADD not in result.chunk.code, "Generic OP_ADD should not be present"

def test_any_addition_bytecode():
    source = "var a: any = 1; var b: any = 2; var c = a + b;"
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

    # Check for the specific opcode
    assert OpCode.OP_ADD in result.chunk.code, "OP_ADD not found in bytecode"
    assert OpCode.OP_ADD_NUMBER not in result.chunk.code, "OP_ADD_NUMBER should not be present"
    assert OpCode.OP_ADD_STRING not in result.chunk.code, "OP_ADD_STRING should not be present"
